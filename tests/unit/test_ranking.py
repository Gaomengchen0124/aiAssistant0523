"""
Ranker 单元测试
"""

import pandas as pd
import pytest

from ranking import Ranker


class TestRankerTopN:
    """测试 Ranker.top_n()"""

    def test_sort_descending(self, composite_df):
        """按 total_score 降序排序"""
        top10 = Ranker.top_n(composite_df)

        scores = top10["total_score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_default_n_is_10(self, composite_df):
        """默认取前 10 名"""
        top10 = Ranker.top_n(composite_df)
        assert len(top10) <= 10

    def test_custom_n(self, composite_df):
        """自定义 N 值"""
        top5 = Ranker.top_n(composite_df, n=5)
        assert len(top5) <= 5

    def test_empty_dataframe(self):
        """空 DataFrame 处理"""
        empty = pd.DataFrame()
        result = Ranker.top_n(empty)
        assert result.empty

    def test_less_than_n_rows(self):
        """数据不足 N 条时返回全部"""
        df = pd.DataFrame({
            "kol_id": ["K1", "K2"],
            "total_score": [80.0, 70.0],
        })
        result = Ranker.top_n(df, n=10)
        assert len(result) == 2

    def test_exactly_n_rows(self):
        """数据恰好 N 条时返回全部"""
        df = pd.DataFrame({
            "kol_id": [f"K{i}" for i in range(10)],
            "total_score": [float(100 - i) for i in range(10)],
        })
        result = Ranker.top_n(df, n=10)
        assert len(result) == 10

    def test_reset_index(self, composite_df):
        """返回结果重置索引"""
        top10 = Ranker.top_n(composite_df)
        assert top10.index.tolist() == list(range(len(top10)))

    def test_top1_highest_score(self, composite_df):
        """第一名分数最高"""
        top10 = Ranker.top_n(composite_df)
        max_score = composite_df["total_score"].max()
        assert top10.iloc[0]["total_score"] == max_score
