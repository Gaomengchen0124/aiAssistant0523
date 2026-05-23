"""
预算分配算法
"""

import pandas as pd


class BudgetAllocator:
    """根据 TOP10 推荐结果分配预算"""

    @staticmethod
    def allocate(
        top10_df: pd.DataFrame,
        total_budget: float,
        top_n: int = 5,
        reserve_ratio: float = 0.20,
    ) -> dict:
        """
        预算分配算法

        Args:
            top10_df: TOP10 达人 DataFrame（含 total_score）
            total_budget: 用户总预算
            top_n: 选择前 N 个达人进行重点投放
            reserve_ratio: 预留测试预算比例（默认 20%）

        Returns:
            {
                "allocations": [
                    {"kol_id": str, "kol_name": str, "allocated": float,
                     "percentage": float, "platform": str, "score": float}
                ],
                "reserve": float,
                "total": float,
                "platform_summary": {"小红书": 2, "抖音": 1, ...}
            }
        """
        if top10_df.empty or total_budget <= 0:
            return {"allocations": [], "reserve": 0, "total": 0, "platform_summary": {}}

        # 1. 取前 N 名
        selected = top10_df.head(top_n).copy()

        # 2. 计算权重（基于匹配分）
        total_score = selected["total_score"].sum()
        if total_score <= 0:
            total_score = 1

        selected["weight"] = selected["total_score"] / total_score

        # 3. 可用预算 = 总预算 × (1 - 预留比例)
        available = total_budget * (1 - reserve_ratio)
        reserve = total_budget * reserve_ratio

        # 4. 分配预算
        allocations = []
        for _, row in selected.iterrows():
            alloc = available * row["weight"]
            allocations.append({
                "kol_id": row["kol_id"],
                "kol_name": row["kol_name"],
                "platform": row["platform"],
                "score": round(float(row["total_score"]), 1),
                "allocated": round(alloc, 0),
                "percentage": round(row["weight"] * 100, 1),
            })

        # 5. 平台汇总
        platform_summary = selected["platform"].value_counts().to_dict()

        return {
            "allocations": allocations,
            "reserve": round(reserve, 0),
            "total": total_budget,
            "platform_summary": platform_summary,
        }

    @staticmethod
    def allocate_by_roi(top10_df: pd.DataFrame, total_budget: float, target_roi: float) -> dict:
        """
        基于期望 ROI 反推可合作的达人组合

        Args:
            top10_df: TOP10 达人 DataFrame
            total_budget: 用户总预算
            target_roi: 期望 ROI（如 3.0 表示 1:3）

        Returns:
            与 allocate() 相同的返回格式
        """
        if top10_df.empty or total_budget <= 0 or target_roi <= 0:
            return {"allocations": [], "reserve": 0, "total": 0, "platform_summary": {}, "message": "参数无效"}

        # 筛选预估 ROI >= 期望 ROI 的达人
        qualified = top10_df[top10_df["conversion_rate"] >= target_roi].copy()

        if qualified.empty:
            # 没有达人达到期望 ROI，返回 ROI 最高的前几个
            qualified = top10_df.head(3).copy()
            message = f"没有达人达到期望 ROI 1:{target_roi}，已推荐 ROI 最高的 {len(qualified)} 位"
        else:
            message = None

        # 按报价升序排序，优先选性价比高的
        qualified = qualified.sort_values("price")

        # 在预算内尽可能多选
        selected = []
        spent = 0
        for _, row in qualified.iterrows():
            if spent + row["price"] <= total_budget * 0.8:  # 预留 20%
                selected.append(row)
                spent += row["price"]
            else:
                break

        if not selected:
            # 预算太少，至少选1个
            selected = [qualified.iloc[0]] if len(qualified) > 0 else []

        selected_df = pd.DataFrame(selected)
        return BudgetAllocator.allocate(selected_df, total_budget, top_n=len(selected))

    @staticmethod
    def format_advice(allocation_result: dict) -> str:
        """将预算分配结果格式化为投放建议文本"""
        lines = ["**预算分配建议**\n"]

        total = allocation_result["total"]
        reserve = allocation_result["reserve"]
        allocs = allocation_result["allocations"]

        lines.append(f"建议总预算：**{total:,.0f} 元**\n")
        lines.append(f"- 重点投放（{len(allocs)} 位达人）：约 {total - reserve:,.0f} 元\n")
        lines.append(f"- 预留测试预算：约 {reserve:,.0f} 元（用于尝试新达人或追加投放）\n\n")

        lines.append("**具体分配：**\n")
        for i, a in enumerate(allocs, 1):
            lines.append(
                f"{i}. **{a['kol_name']}**（{a['platform']}）："
                f"{a['allocated']:,.0f} 元（占 {a['percentage']:.0f}%）\n"
            )

        lines.append("\n**平台分布：**\n")
        for platform, count in allocation_result["platform_summary"].items():
            lines.append(f"- {platform}：{count} 位达人\n")

        return "".join(lines)


if __name__ == "__main__":
    from csv_loader import CSVLoader
    from filters import CandidateFilter, DemandParser
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

    result = BudgetAllocator.allocate(top10, total_budget=15000)
    print(f"[OK] Allocated to {len(result['allocations'])} KOLs")
    print(f"[OK] Reserve: {result['reserve']:.0f} yuan")
    print("\n" + BudgetAllocator.format_advice(result))
