"""
数据质量验证测试
"""

import pandas as pd
import pytest

from csv_loader import CSVLoader


class TestDataQuality:
    """测试 CSV 数据质量"""

    @pytest.fixture
    def df(self, test_csv_path):
        loader = CSVLoader(test_csv_path)
        return loader.load()

    def test_all_required_columns_present(self, df):
        """所有必填列存在"""
        required = [
            "kol_id", "kol_name", "platform", "followers", "field",
            "price", "avg_likes", "avg_comments", "engagement_rate",
            "conversion_rate", "audience", "cooperation_count", "risk_note",
        ]
        for col in required:
            assert col in df.columns, f"缺少列: {col}"

    def test_no_duplicate_kol_ids(self, df):
        """无重复 kol_id"""
        assert df["kol_id"].is_unique

    def test_no_empty_kol_id(self, df):
        """kol_id 无空值"""
        assert df["kol_id"].notna().all()
        assert (df["kol_id"] != "").all()

    def test_followers_positive(self, df):
        """粉丝数为正"""
        assert (df["followers"] > 0).all()

    def test_price_positive(self, df):
        """报价为正"""
        assert (df["price"] > 0).all()

    def test_engagement_rate_range(self, df):
        """互动率在合理范围（0-100%）"""
        assert (df["engagement_rate"] >= 0).all()
        assert (df["engagement_rate"] <= 100).all()

    def test_conversion_rate_range(self, df):
        """转化率在合理范围（0-100%）"""
        assert (df["conversion_rate"] >= 0).all()
        assert (df["conversion_rate"] <= 100).all()

    def test_platform_enum(self, df):
        """平台值在枚举范围内"""
        valid_platforms = {"小红书", "抖音", "B站", "微博"}
        assert set(df["platform"].unique()).issubset(valid_platforms)

    def test_cooperation_count_non_negative(self, df):
        """合作次数非负"""
        assert (df["cooperation_count"] >= 0).all()

    def test_avg_likes_non_negative(self, df):
        """平均点赞数非负"""
        assert (df["avg_likes"] >= 0).all()

    def test_avg_comments_non_negative(self, df):
        """平均评论数非负"""
        assert (df["avg_comments"] >= 0).all()

    def test_risk_note_not_empty(self, df):
        """风险备注无空值"""
        assert df["risk_note"].notna().all()
        assert (df["risk_note"] != "").all()

    def test_data_sufficient_volume(self, df):
        """数据量足够（至少 10 条）"""
        assert len(df) >= 10

    def test_kol_name_not_empty(self, df):
        """达人名称无空值"""
        assert df["kol_name"].notna().all()
        assert (df["kol_name"] != "").all()

    def test_audience_not_empty(self, df):
        """受众画像无空值"""
        assert df["audience"].notna().all()
        assert (df["audience"] != "").all()

    def test_field_not_empty(self, df):
        """内容领域无空值"""
        assert df["field"].notna().all()
        assert (df["field"] != "").all()

    def test_price_reasonable_range(self, df):
        """报价在合理范围"""
        assert (df["price"] >= 500).all()
        assert (df["price"] <= 50000).all()

    def test_engagement_rate_reasonable(self, df):
        """互动率不过高（不超过 20%）"""
        assert (df["engagement_rate"] <= 20).all()

    def test_conversion_rate_reasonable(self, df):
        """转化率不过高（不超过 10%）"""
        assert (df["conversion_rate"] <= 10).all()
