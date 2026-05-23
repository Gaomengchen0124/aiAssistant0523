"""
输出格式化：Markdown 表格 + 投放建议
"""

import pandas as pd

from roi_calculator import ROICalculator


class OutputFormatter:
    """格式化最终推荐报告"""

    @staticmethod
    def to_markdown(top10_df: pd.DataFrame, advice_text: str) -> str:
        """生成 Markdown 格式的推荐报告"""
        if top10_df.empty:
            return "未找到符合条件的达人，请放宽筛选条件。"

        lines = []

        # 投放建议（保留 LLM 生成的内容）
        lines.append("## 投放建议\n")
        lines.append(advice_text)
        lines.append("")
        lines.append("## 注意事项\n")
        lines.append("1. 最终投放决策需人工复核，重点核实排名前 3 达人的数据真实性\n")
        lines.append("2. 首次合作建议签订详细合作协议，明确内容要求和发布时间\n")
        lines.append("3. 投放后建议追踪转化数据，为下次投放积累经验\n")
        lines.append("")
        lines.append("> **人工复核提示**：最终投放决策需人工复核。"
        )

        return "\n".join(lines)

    @staticmethod
    def _format_followers(num: int) -> str:
        """粉丝数格式化：50000 -> 5万"""
        if num >= 10000:
            return f"{num / 10000:.0f}万"
        return str(num)


if __name__ == "__main__":
    from csv_loader import CSVLoader
    from filters import DemandParser, CandidateFilter
    from scoring import ValueScorer, RiskAssessor, CompositeScorer
    from ranking import Ranker

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

    advice = "建议优先选择前3名达人，预算分配 60% 给高匹配度达人，预留 20% 测试新达人。"
    md = OutputFormatter.to_markdown(top10, advice)
    print(md)
