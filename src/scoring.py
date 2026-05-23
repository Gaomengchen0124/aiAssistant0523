"""
评分系统：受众匹配 / 性价比 / 风险 / 综合评分
"""

import pandas as pd


class AudienceMatcher:
    """受众匹配度计算（依赖LLM，占位）"""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def match(self, audience_text: str, target_audience: str) -> float:
        """计算受众匹配度（0-100分）

        若未提供 LLM 客户端，使用简化规则匹配
        """
        if self.llm_client is None:
            # 简化规则：关键词重叠度
            return self._rule_based_match(audience_text, target_audience)

        # LLM 匹配（在 kol-007 中实现）
        return self.llm_client.match_audience(audience_text, target_audience)

    @staticmethod
    def _rule_based_match(audience_text: str, target_audience: str) -> float:
        """基于关键词重叠的简化匹配"""
        aud_set = set(str(audience_text).lower().split("、"))
        tgt_set = set(str(target_audience).lower().split(","))
        # 取并集作为分母
        union = aud_set | tgt_set
        if not union:
            return 50.0
        overlap = aud_set & tgt_set
        score = len(overlap) / len(union) * 100
        return min(max(score, 30.0), 95.0)


class ValueScorer:
    """性价比得分计算（互动率×转化率×粉丝数/报价）"""

    @staticmethod
    def score(df: pd.DataFrame) -> pd.DataFrame:
        """计算性价比得分并归一化到 0-100"""
        df = df.copy()

        # 公式: (互动率 × 转化率 × 粉丝数) / 报价
        df["value_raw"] = (
            df["engagement_rate"] * df["conversion_rate"] * df["followers"]
        ) / df["price"]

        # Min-Max 归一化到 0-100
        min_val = df["value_raw"].min()
        max_val = df["value_raw"].max()
        if max_val > min_val:
            df["value_score"] = (df["value_raw"] - min_val) / (max_val - min_val) * 100
        else:
            df["value_score"] = 50.0

        return df


class RiskAssessor:
    """风险评估：文本备注 → 低/中/高 → 扣分"""

    RISK_KEYWORDS = {
        "高": ["广告比例较高", "数据异常", "粉丝质量存疑"],
        "中": ["需谨慎", "有争议"],
        "低": ["数据真实", "无风险"],
    }

    @classmethod
    def assess(cls, risk_note: str) -> tuple[str, int]:
        """
        评估风险等级和扣分

        Returns:
            (风险等级, 扣分)
        """
        note = str(risk_note)

        for level, keywords in cls.RISK_KEYWORDS.items():
            for kw in keywords:
                if kw in note:
                    if level == "高":
                        return "高", 10
                    elif level == "中":
                        return "中", 5
                    else:
                        return "低", 0

        return "低", 0

    @classmethod
    def assess_batch(cls, df: pd.DataFrame) -> pd.DataFrame:
        """批量评估风险"""
        df = df.copy()
        results = df["risk_note"].apply(cls.assess)
        df["risk_level"] = [r[0] for r in results]
        df["risk_penalty"] = [r[1] for r in results]
        return df


class CompositeScorer:
    """综合评分：匹配40% + 性价比35% + 风险25%"""

    WEIGHTS = {
        "match": 0.40,
        "value": 0.35,
        "risk": 0.25,
    }

    @staticmethod
    def compute(df: pd.DataFrame, match_scores: dict[str, float] = None) -> pd.DataFrame:
        """
        计算综合评分

        Args:
            df: 包含 value_score, risk_penalty 的 DataFrame
            match_scores: 可选，{kol_id: match_score} 受众匹配分

        Returns:
            添加 total_score 列的 DataFrame
        """
        df = df.copy()

        # 确保有性价比分
        if "value_score" not in df.columns:
            df = ValueScorer.score(df)

        # 确保有风险扣分
        if "risk_penalty" not in df.columns:
            df = RiskAssessor.assess_batch(df)

        # 受众匹配分
        if match_scores:
            df["match_score"] = df["kol_id"].map(match_scores).fillna(50.0)
        else:
            df["match_score"] = 50.0

        # 风险得分 = 100 - 扣分
        df["risk_score"] = 100 - df["risk_penalty"]

        # 综合评分
        w = CompositeScorer.WEIGHTS
        df["total_score"] = (
            df["match_score"] * w["match"] +
            df["value_score"] * w["value"] +
            df["risk_score"] * w["risk"]
        )

        # 限制在 0-100
        df["total_score"] = df["total_score"].clip(0, 100)

        return df


if __name__ == "__main__":
    from csv_loader import CSVLoader
    from filters import CandidateFilter, DemandParser

    loader = CSVLoader()
    df = loader.load()

    demand = DemandParser.parse({
        "target_audience": "大学生",
        "content_field": "校园",
        "budget_range": "1000-5000",
        "platforms": "小红书,抖音,B站,微博",
    })

    candidates = CandidateFilter.filter(df, demand)
    print(f"[OK] Candidates: {len(candidates)}")

    # 性价比评分
    scored = ValueScorer.score(candidates)
    print("\n[Value Score TOP 3]")
    print(scored.nlargest(3, "value_score")[["kol_name", "value_score"]].to_string(index=False))

    # 风险评估
    risked = RiskAssessor.assess_batch(scored)
    print("\n[Risk Distribution]")
    print(risked["risk_level"].value_counts().to_string())

    # 综合评分（无LLM匹配分，默认50）
    final = CompositeScorer.compute(risked)
    print("\n[Composite Score TOP 5]")
    print(final.nlargest(5, "total_score")[["kol_name", "match_score", "value_score", "risk_score", "total_score"]].to_string(index=False))
