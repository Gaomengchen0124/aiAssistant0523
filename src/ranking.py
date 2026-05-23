"""
TOP 10 排序筛选
"""

import pandas as pd


class Ranker:
    """按综合评分排序，取前10"""

    @staticmethod
    def top_n(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """按 total_score 降序排序，取前 n 名"""
        if df.empty:
            return df
        return df.sort_values("total_score", ascending=False).head(n).reset_index(drop=True)


if __name__ == "__main__":
    from csv_loader import CSVLoader
    from filters import DemandParser, CandidateFilter
    from scoring import ValueScorer, RiskAssessor, CompositeScorer

    loader = CSVLoader()
    df = loader.load()
    demand = DemandParser.parse({
        "target_audience": "大学生",
        "content_field": "校园",
        "budget_range": "1000-5000",
        "platforms": "小红书,抖音,B站,微博",
    })
    candidates = CandidateFilter.filter(df, demand)
    scored = ValueScorer.score(candidates)
    risked = RiskAssessor.assess_batch(scored)
    final = CompositeScorer.compute(risked)
    top10 = Ranker.top_n(final)
    print(f"TOP 10 数量: {len(top10)}")
    print(top10[["kol_name", "platform", "total_score"]].to_string(index=False))
