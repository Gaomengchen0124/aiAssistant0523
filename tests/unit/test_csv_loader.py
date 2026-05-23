"""
CSVLoader 单元测试
"""

from pathlib import Path

import pandas as pd
import pytest

from csv_loader import CSVLoader


class TestCSVLoaderLoad:
    """测试 CSVLoader.load()"""

    def test_load_valid_csv(self, test_csv_path):
        """正常加载 CSV 文件"""
        loader = CSVLoader(test_csv_path)
        df = loader.load()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 20
        assert "kol_id" in df.columns
        assert df["kol_id"].dtype == object

    def test_load_nonexistent_file(self):
        """文件不存在时抛出 FileNotFoundError"""
        loader = CSVLoader("nonexistent.csv")
        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_numeric_columns_conversion(self, test_csv_path):
        """数值字段正确转换为数值类型"""
        loader = CSVLoader(test_csv_path)
        df = loader.load()

        numeric_cols = [
            "followers", "price", "avg_likes", "avg_comments",
            "engagement_rate", "conversion_rate", "cooperation_count",
        ]
        for col in numeric_cols:
            assert df[col].dtype in ["int64", "float64", "Int64"]


class TestCSVLoaderValidate:
    """测试 CSVLoader.validate()"""

    def test_validate_valid_data(self, test_csv_path):
        """有效数据验证通过"""
        loader = CSVLoader(test_csv_path)
        df = loader.load()
        ok, errs = loader.validate(df)

        assert ok is True
        assert errs == []

    def test_validate_missing_columns(self, test_csv_path):
        """缺少必填列时返回错误"""
        loader = CSVLoader(test_csv_path)
        df = loader.load()
        df_missing = df.drop(columns=["kol_name", "platform"])

        ok, errs = loader.validate(df_missing)
        assert ok is False
        assert any("缺少必填列" in e for e in errs)
        assert any("kol_name" in e for e in errs)
        assert any("platform" in e for e in errs)

    def test_validate_null_values(self, test_csv_path):
        """存在空值时返回错误"""
        loader = CSVLoader(test_csv_path)
        df = loader.load()
        df_with_null = df.copy()
        df_with_null.loc[0, "kol_name"] = None

        ok, errs = loader.validate(df_with_null)
        assert ok is False
        assert any("空值" in e for e in errs)

    def test_validate_too_few_rows(self, test_csv_path):
        """数据量过少时返回错误"""
        loader = CSVLoader(test_csv_path)
        df = loader.load()
        df_small = df.head(5)

        ok, errs = loader.validate(df_small)
        assert ok is False
        assert any("数据量过少" in e for e in errs)

    def test_validate_all_null_column(self, test_csv_path):
        """某列全部为空时返回错误"""
        loader = CSVLoader(test_csv_path)
        df = loader.load()
        df_all_null = df.copy()
        df_all_null["kol_name"] = None

        ok, errs = loader.validate(df_all_null)
        assert ok is False
        assert any("空值" in e for e in errs)
