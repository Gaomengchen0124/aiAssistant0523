"""
KOLPipeline 单元测试
"""

import pytest

from pipeline import KOLPipeline


class TestKOLPipelineInit:
    """测试 KOLPipeline 初始化"""

    def test_init_without_llm(self, test_csv_path):
        """不使用 LLM 时正常初始化"""
        pipeline = KOLPipeline(csv_path=test_csv_path, use_llm=False)
        assert pipeline.use_llm is False
        assert pipeline.llm_client is None

    def test_init_llm_failure_fallback(self, test_csv_path, monkeypatch):
        """LLM 初始化失败时降级为规则匹配"""
        import pipeline as pipeline_mod

        def raise_error(*a, **k):
            raise ValueError("No API key")

        monkeypatch.setattr(pipeline_mod, "LLMClient", raise_error)

        pipeline = KOLPipeline(csv_path=test_csv_path, use_llm=True)
        assert pipeline.use_llm is False
        assert pipeline.llm_client is None


class TestKOLPipelineRun:
    """测试 KOLPipeline.run()"""

    def test_run_with_form_data(self, mock_pipeline, sample_form_data):
        """完整流程端到端测试（使用 mock LLM）"""
        report = mock_pipeline.run(sample_form_data)

        assert "投放建议" in report
        assert "人工复核" in report
        assert mock_pipeline.top10 is not None
        assert len(mock_pipeline.top10) > 0

    def test_run_with_text_input(self, mock_pipeline):
        """自然语言输入测试"""
        text = "我们要找小红书达人，目标受众大学生，预算1000-3000元"
        report = mock_pipeline.run(text)

        assert "投放建议" in report or "未找到" in report

    def test_run_empty_candidates(self, mock_pipeline):
        """空候选人时返回提示"""
        form_data = {
            "target_audience": "大学生",
            "content_field": "不存在的领域",
            "budget_range": "1000-3000",
            "platforms": "小红书",
        }
        report = mock_pipeline.run(form_data)

        assert "未找到符合条件的达人" in report

    def test_run_creates_top10(self, mock_pipeline, sample_form_data):
        """运行后生成 top10"""
        mock_pipeline.run(sample_form_data)

        assert mock_pipeline.top10 is not None
        assert len(mock_pipeline.top10) <= 10

    def test_run_columns_in_top10(self, mock_pipeline, sample_form_data):
        """top10 包含所有必需列"""
        mock_pipeline.run(sample_form_data)

        required_cols = [
            "kol_id", "kol_name", "platform", "followers", "price",
            "total_score", "roi", "risk_level", "recommend_reason",
        ]
        for col in required_cols:
            assert col in mock_pipeline.top10.columns

    def test_top10_sorted_by_score(self, mock_pipeline, sample_form_data):
        """top10 按匹配分降序排序"""
        mock_pipeline.run(sample_form_data)

        scores = mock_pipeline.top10["total_score"].tolist()
        assert scores == sorted(scores, reverse=True)


class TestKOLPipelineFallback:
    """测试降级方法"""

    def test_fallback_reason_format(self):
        """_fallback_reason 输出格式包含关键数据"""
        row = {
            "match_score": 85,
            "engagement_rate": 4.0,
            "conversion_rate": 3.5,
            "cooperation_count": 30,
        }
        reason = KOLPipeline._fallback_reason(row)

        assert "受众" in reason
        assert "互动率" in reason
        assert "转化率" in reason
        assert "合作" in reason

    def test_fallback_reason_high_match(self):
        """高匹配分时输出受众高度匹配"""
        row = {"match_score": 85, "engagement_rate": 4.0, "conversion_rate": 3.5, "cooperation_count": 30}
        reason = KOLPipeline._fallback_reason(row)
        assert "高度匹配" in reason

    def test_fallback_reason_medium_match(self):
        """中匹配分时输出受众部分匹配"""
        row = {"match_score": 70, "engagement_rate": 4.0, "conversion_rate": 3.5, "cooperation_count": 30}
        reason = KOLPipeline._fallback_reason(row)
        assert "部分匹配" in reason

    def test_fallback_reason_low_match(self):
        """低匹配分时输出受众有一定重合"""
        row = {"match_score": 50, "engagement_rate": 4.0, "conversion_rate": 3.5, "cooperation_count": 30}
        reason = KOLPipeline._fallback_reason(row)
        assert "有一定重合" in reason

    def test_fallback_advice_contains_three_sections(self):
        """_fallback_advice 包含三部分建议"""
        advice = KOLPipeline._fallback_advice()

        assert "预算分配建议" in advice
        assert "平台组合建议" in advice
        assert "注意事项" in advice

    def test_fallback_advice_contains_budget_ratio(self):
        """预算分配建议包含 60% 比例"""
        advice = KOLPipeline._fallback_advice()
        assert "60%" in advice

    def test_fallback_advice_contains_platform_names(self):
        """平台组合建议包含平台名称"""
        advice = KOLPipeline._fallback_advice()
        assert "小红书" in advice
        assert "抖音" in advice
        assert "B站" in advice

    def test_fallback_advice_contains_risk_warning(self):
        """注意事项包含风险提示"""
        advice = KOLPipeline._fallback_advice()
        assert "原创内容" in advice
