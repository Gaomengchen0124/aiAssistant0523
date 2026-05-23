"""
端到端集成测试
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pipeline import KOLPipeline


class TestEndToEndPipeline:
    """测试完整推荐流程"""

    def test_standard_demand_produces_top10(self, mock_pipeline, sample_form_data):
        """标准需求输入产生 TOP 10 输出"""
        report = mock_pipeline.run(sample_form_data)

        assert mock_pipeline.top10 is not None
        assert len(mock_pipeline.top10) > 0
        assert len(mock_pipeline.top10) <= 10

    def test_output_contains_required_columns(self, mock_pipeline, sample_form_data):
        """输出包含所有必需字段"""
        mock_pipeline.run(sample_form_data)
        top10 = mock_pipeline.top10

        required_cols = [
            "kol_id", "kol_name", "platform", "followers", "price",
            "total_score", "roi", "risk_level", "recommend_reason",
        ]
        for col in required_cols:
            assert col in top10.columns, f"缺少列: {col}"

    def test_sorted_by_total_score_descending(self, mock_pipeline, sample_form_data):
        """按匹配分降序排序"""
        mock_pipeline.run(sample_form_data)
        scores = mock_pipeline.top10["total_score"].tolist()

        assert scores == sorted(scores, reverse=True)

    def test_platform_filter_applied(self, mock_pipeline):
        """平台筛选生效"""
        form_data = {
            "target_audience": "大学生和应届生",
            "content_field": "校园",
            "budget_range": "1000-3000",
            "platforms": "小红书",
            "engagement_rate_min": "3.0",
        }
        mock_pipeline.run(form_data)

        platforms = mock_pipeline.top10["platform"].unique()
        assert set(platforms) == {"小红书"}

    def test_budget_filter_applied(self, mock_pipeline, sample_form_data):
        """预算筛选生效"""
        mock_pipeline.run(sample_form_data)

        for _, row in mock_pipeline.top10.iterrows():
            assert 1000 <= row["price"] <= 3000

    def test_risk_annotated(self, mock_pipeline, sample_form_data):
        """风险提示标注"""
        mock_pipeline.run(sample_form_data)

        assert "risk_level" in mock_pipeline.top10.columns
        risk_levels = mock_pipeline.top10["risk_level"].unique()
        assert set(risk_levels).issubset({"高", "中", "低"})

    def test_roi_computed(self, mock_pipeline, sample_form_data):
        """ROI 已计算"""
        mock_pipeline.run(sample_form_data)

        assert "roi" in mock_pipeline.top10.columns
        for roi in mock_pipeline.top10["roi"]:
            assert roi.startswith("1:")

    def test_report_contains_advice(self, mock_pipeline, sample_form_data):
        """报告包含投放建议"""
        report = mock_pipeline.run(sample_form_data)

        assert "投放建议" in report or "预算分配" in report

    def test_report_contains_manual_review(self, mock_pipeline, sample_form_data):
        """报告包含人工复核提示"""
        report = mock_pipeline.run(sample_form_data)

        assert "人工复核" in report

    def test_multi_platform_distribution(self, mock_pipeline):
        """多平台支持：推荐列表包含多个平台"""
        form_data = {
            "target_audience": "大学生和应届生",
            "content_field": "校园",
            "budget_range": "1000-5000",
            "platforms": "小红书,抖音,B站,微博",
            "engagement_rate_min": "3.0",
        }
        mock_pipeline.run(form_data)

        platforms = set(mock_pipeline.top10["platform"].unique())
        # 至少包含 2 个不同平台
        assert len(platforms) >= 2

    def test_score_in_valid_range(self, mock_pipeline, sample_form_data):
        """匹配分数在 0-100 之间"""
        mock_pipeline.run(sample_form_data)

        scores = mock_pipeline.top10["total_score"]
        assert scores.min() >= 0
        assert scores.max() <= 100

    def test_no_candidates_returns_message(self, mock_pipeline):
        """无候选人时返回提示信息"""
        form_data = {
            "target_audience": "大学生",
            "content_field": "不存在领域",
            "budget_range": "1000-3000",
            "platforms": "小红书",
        }
        report = mock_pipeline.run(form_data)

        assert "未找到符合条件的达人" in report

    def test_pipeline_steps_executed_in_order(self, mock_pipeline, sample_form_data):
        """各步骤按顺序执行，生成完整结果"""
        report = mock_pipeline.run(sample_form_data)

        assert mock_pipeline.demand is not None
        assert mock_pipeline.candidates is not None
        assert mock_pipeline.top10 is not None
        assert len(mock_pipeline.top10) <= 10
