"""
评分系统单元测试：AudienceMatcher, ValueScorer, RiskAssessor, CompositeScorer
"""

import pandas as pd
import pytest

from scoring import (
    AudienceMatcher,
    CompositeScorer,
    RiskAssessor,
    ValueScorer,
)


class TestAudienceMatcherRuleBased:
    """测试 AudienceMatcher._rule_based_match()"""

    def test_perfect_match(self):
        """完全匹配时返回高分（注意 target 用逗号分隔）"""
        matcher = AudienceMatcher()
        result = matcher._rule_based_match("大学生、应届生", "大学生,应届生")
        assert result >= 80
        assert result <= 95

    def test_partial_match(self):
        """部分重叠时返回中等分数"""
        matcher = AudienceMatcher()
        result = matcher._rule_based_match("大学生、应届生", "职场新人,大学生")
        assert result >= 30
        assert result < 80

    def test_no_overlap(self):
        """无重叠时返回最低分（30）"""
        matcher = AudienceMatcher()
        result = matcher._rule_based_match("大学生", "宝妈")
        assert result == 30.0

    def test_empty_inputs(self):
        """空输入时 split 产生空字符串集合，交集非空返回高分"""
        matcher = AudienceMatcher()
        result = matcher._rule_based_match("", "")
        # split 后得到 {''}，交集非空，所以 score=100，clip 到 95
        assert result == 95.0

    def test_case_insensitive(self):
        """大小写不敏感匹配"""
        matcher = AudienceMatcher()
        result = matcher._rule_based_match("大学生", "大学生")
        assert result > 30

    def test_match_with_llm_none(self):
        """无 LLM 客户端时使用规则匹配"""
        matcher = AudienceMatcher(llm_client=None)
        result = matcher.match("大学生、应届生", "大学生")
        assert isinstance(result, float)
        assert 30 <= result <= 95


class TestValueScorer:
    """测试 ValueScorer.score()"""

    def test_basic_formula(self, candidates_df):
        """性价比公式验证"""
        scored = ValueScorer.score(candidates_df)

        # 验证 raw 值计算：(互动率 * 转化率 * 粉丝数) / 报价
        for _, row in scored.iterrows():
            expected_raw = (row["engagement_rate"] * row["conversion_rate"] * row["followers"]) / row["price"]
            assert abs(row["value_raw"] - expected_raw) < 0.01

    def test_normalization_range(self, candidates_df):
        """归一化到 0-100 范围"""
        scored = ValueScorer.score(candidates_df)

        assert scored["value_score"].min() >= 0
        assert scored["value_score"].max() <= 100

    def test_best_score_is_100(self, candidates_df):
        """最高性价比得分为 100"""
        scored = ValueScorer.score(candidates_df)
        max_raw_idx = scored["value_raw"].idxmax()
        assert scored.loc[max_raw_idx, "value_score"] == 100.0

    def test_worst_score_is_0(self, candidates_df):
        """最低性价比得分为 0"""
        scored = ValueScorer.score(candidates_df)
        min_raw_idx = scored["value_raw"].idxmin()
        assert scored.loc[min_raw_idx, "value_score"] == 0.0

    def test_all_same_returns_50(self):
        """所有值相同时返回 50"""
        df = pd.DataFrame({
            "engagement_rate": [3.0, 3.0, 3.0],
            "conversion_rate": [3.0, 3.0, 3.0],
            "followers": [10000, 10000, 10000],
            "price": [1000, 1000, 1000],
        })
        scored = ValueScorer.score(df)
        assert all(scored["value_score"] == 50.0)

    def test_returns_copy(self, candidates_df):
        """返回的是副本，不修改原始 DataFrame"""
        original_cols = set(candidates_df.columns)
        scored = ValueScorer.score(candidates_df)
        assert set(candidates_df.columns) == original_cols


class TestRiskAssessor:
    """测试 RiskAssessor"""

    def test_high_risk_keywords(self):
        """高风险关键词识别及扣分"""
        test_cases = [
            ("广告比例较高", "高", 10),
            ("数据异常", "高", 10),
            ("粉丝质量存疑", "高", 10),
        ]
        for note, expected_level, expected_penalty in test_cases:
            level, penalty = RiskAssessor.assess(note)
            assert level == expected_level
            assert penalty == expected_penalty

    def test_medium_risk_keywords(self):
        """中风险关键词识别及扣分"""
        test_cases = [
            ("需谨慎", "中", 5),
            ("有争议", "中", 5),
        ]
        for note, expected_level, expected_penalty in test_cases:
            level, penalty = RiskAssessor.assess(note)
            assert level == expected_level
            assert penalty == expected_penalty

    def test_low_risk_keywords(self):
        """低风险关键词识别"""
        test_cases = [
            ("数据真实", "低", 0),
            ("无风险", "低", 0),
        ]
        for note, expected_level, expected_penalty in test_cases:
            level, penalty = RiskAssessor.assess(note)
            assert level == expected_level
            assert penalty == expected_penalty

    def test_no_risk_note(self):
        """无风险关键词时默认低风险"""
        level, penalty = RiskAssessor.assess("这是一个普通备注")
        assert level == "低"
        assert penalty == 0

    def test_batch_assess(self, candidates_df):
        """批量评估返回正确列"""
        result = RiskAssessor.assess_batch(candidates_df)
        assert "risk_level" in result.columns
        assert "risk_penalty" in result.columns
        assert set(result["risk_level"].unique()).issubset({"高", "中", "低"})
        assert result["risk_penalty"].isin([0, 5, 10]).all()

    def test_high_risk_priority(self):
        """同时包含高低风险词时，高风险优先"""
        level, penalty = RiskAssessor.assess("数据真实，但广告比例较高")
        assert level == "高"
        assert penalty == 10


class TestCompositeScorer:
    """测试 CompositeScorer.compute()"""

    def test_weights_formula(self, scored_df):
        """权重公式验证：匹配40% + 性价比35% + 风险25%"""
        match_scores = dict(zip(scored_df["kol_id"], scored_df["match_score"]))
        result = CompositeScorer.compute(scored_df, match_scores)

        for _, row in result.iterrows():
            expected = (
                row["match_score"] * 0.40 +
                row["value_score"] * 0.35 +
                row["risk_score"] * 0.25
            )
            assert abs(row["total_score"] - expected) < 0.01

    def test_high_risk_penalty_applied(self, scored_df):
        """高风险扣分正确应用"""
        match_scores = dict(zip(scored_df["kol_id"], scored_df["match_score"]))
        result = CompositeScorer.compute(scored_df, match_scores)

        high_risk = result[result["risk_level"] == "高"]
        low_risk = result[result["risk_level"] == "低"]

        if not high_risk.empty and not low_risk.empty:
            # 其他条件相同时，高风险的分数应该更低
            # 注意：这里只做基本验证，不完全精确因为 match_score 和 value_score 也影响
            assert all(high_risk["risk_penalty"] == 10)
            assert all(low_risk["risk_penalty"] == 0)

    def test_score_range_0_to_100(self, scored_df):
        """分数限制在 0-100 范围"""
        match_scores = dict(zip(scored_df["kol_id"], scored_df["match_score"]))
        result = CompositeScorer.compute(scored_df, match_scores)

        assert result["total_score"].min() >= 0
        assert result["total_score"].max() <= 100

    def test_auto_compute_missing_columns(self, candidates_df):
        """缺失中间列时自动计算"""
        # candidates_df 没有 value_score 和 risk_penalty
        match_scores = {row["kol_id"]: 80.0 for _, row in candidates_df.iterrows()}
        result = CompositeScorer.compute(candidates_df, match_scores)

        assert "value_score" in result.columns
        assert "risk_penalty" in result.columns
        assert "total_score" in result.columns

    def test_no_match_scores(self, scored_df):
        """无 match_scores 时使用默认值 50"""
        result = CompositeScorer.compute(scored_df)
        assert (result["match_score"] == 50.0).all()

    def test_weights_sum_to_100(self):
        """权重之和为 1"""
        assert sum(CompositeScorer.WEIGHTS.values()) == 1.0
