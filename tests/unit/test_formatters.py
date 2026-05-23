"""
OutputFormatter 单元测试
"""

import pandas as pd
import pytest

from formatters import OutputFormatter


class TestOutputFormatterToMarkdown:
    """测试 OutputFormatter.to_markdown()"""

    def test_contains_advice(self, composite_df):
        """输出包含投放建议"""
        top10 = composite_df.head(3).copy()
        top10["roi"] = "1:2.9"
        top10["recommend_reason"] = "测试推荐理由"
        top10["risk_level"] = "低"

        advice = "这是投放建议内容"
        report = OutputFormatter.to_markdown(top10, advice)

        assert "投放建议" in report
        assert advice in report

    def test_contains_manual_review_warning(self, composite_df):
        """包含人工复核提示"""
        top10 = composite_df.head(1).copy()
        top10["roi"] = "1:2.9"
        top10["recommend_reason"] = "测试"
        top10["risk_level"] = "低"

        report = OutputFormatter.to_markdown(top10, "建议")

        assert "人工复核" in report
        assert "最终投放决策需人工复核" in report

    def test_contains_notes_section(self, composite_df):
        """输出包含注意事项"""
        top10 = composite_df.head(1).copy()
        top10["roi"] = "1:2.9"
        top10["recommend_reason"] = "测试"
        top10["risk_level"] = "低"

        report = OutputFormatter.to_markdown(top10, "建议")

        assert "注意事项" in report
        assert "数据真实性" in report
        assert "合作协议" in report
        assert "转化数据" in report

    def test_empty_dataframe(self):
        """空 DataFrame 返回提示信息"""
        empty = pd.DataFrame()
        report = OutputFormatter.to_markdown(empty, "建议")
        assert "未找到符合条件的达人" in report

    def test_advice_text_in_output(self):
        """传入的 advice_text 出现在输出中"""
        df = pd.DataFrame({"kol_id": ["K1"]})
        advice = "自定义投放建议"
        report = OutputFormatter.to_markdown(df, advice)

        assert advice in report


class TestOutputFormatterFormatFollowers:
    """测试 OutputFormatter._format_followers()"""

    def test_below_10000(self):
        """万以下直接返回数字"""
        assert OutputFormatter._format_followers(5000) == "5000"
        assert OutputFormatter._format_followers(9999) == "9999"

    def test_exactly_10000(self):
        """恰好 1 万"""
        assert OutputFormatter._format_followers(10000) == "1万"

    def test_above_10000(self):
        """万以上转换为 X万"""
        assert OutputFormatter._format_followers(50000) == "5万"
        assert OutputFormatter._format_followers(120000) == "12万"

    def test_zero(self):
        """0 粉丝"""
        assert OutputFormatter._format_followers(0) == "0"
