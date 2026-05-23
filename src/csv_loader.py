"""
CSV 数据加载与清洗
"""

import pandas as pd
from pathlib import Path


class CSVLoader:
    """加载达人数据库CSV"""

    REQUIRED_COLUMNS = [
        "kol_id", "kol_name", "platform", "followers", "field",
        "price", "avg_likes", "avg_comments", "engagement_rate",
        "conversion_rate", "audience", "cooperation_count", "risk_note",
    ]

    NUMERIC_COLUMNS = [
        "followers", "price", "avg_likes", "avg_comments",
        "engagement_rate", "conversion_rate", "cooperation_count",
    ]

    def __init__(self, csv_path: str = "data/influencers.csv"):
        self.csv_path = Path(csv_path)

    def load(self) -> pd.DataFrame:
        """读取 CSV 并进行字段类型转换"""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {self.csv_path.absolute()}")

        df = pd.read_csv(self.csv_path, dtype={"kol_id": str})

        # 数值字段转换
        for col in self.NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def validate(self, df: pd.DataFrame) -> tuple[bool, list[str]]:
        """检查必填字段完整性

        Returns:
            (是否通过, 错误信息列表)
        """
        errors = []

        # 检查必填列
        missing_cols = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            errors.append(f"缺少必填列: {missing_cols}")

        # 检查空值
        for col in self.REQUIRED_COLUMNS:
            if col in df.columns and df[col].isnull().any():
                null_rows = df[df[col].isnull()].index.tolist()
                errors.append(f"列 '{col}' 存在空值，行索引: {null_rows}")

        # 检查数据量
        if len(df) < 10:
            errors.append(f"数据量过少: 仅 {len(df)} 条记录，建议至少 80 条")

        return len(errors) == 0, errors


if __name__ == "__main__":
    loader = CSVLoader()
    data = loader.load()
    ok, errs = loader.validate(data)
    print(f"[OK] Loaded {len(data)} records")
    print(f"[OK] Validation passed" if ok else f"[FAIL] Validation failed")
    if errs:
        for e in errs:
            print(f"  - {e}")
