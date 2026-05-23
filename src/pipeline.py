"""
KOL Matcher - 11步原子工作流编排器
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from csv_loader import CSVLoader
from filters import CandidateFilter, Demand, DemandParser
from formatters import OutputFormatter
from llm_client import LLMClient
from ranking import Ranker
from roi_calculator import ROICalculator
from scoring import AudienceMatcher, CompositeScorer, RiskAssessor, ValueScorer

load_dotenv()


class KOLPipeline:
    """达人推荐流程编排"""

    def __init__(self, csv_path: str = "data/influencers.csv", use_llm: bool = True):
        self.csv_path = csv_path
        self.use_llm = use_llm
        self.llm_client: LLMClient | None = None
        if use_llm:
            try:
                self.llm_client = LLMClient()
            except ValueError as e:
                print(f"[警告] LLM 初始化失败: {e}，将使用规则匹配")
                self.use_llm = False

        self.data: pd.DataFrame | None = None
        self.demand: Demand | None = None
        self.candidates: pd.DataFrame | None = None
        self.top10: pd.DataFrame | None = None

    def run(self, demand_input: dict | str) -> str:
        """
        执行完整的推荐流程

        Args:
            demand_input: 字典（表单数据）或字符串（自然语言）

        Returns:
            Markdown 格式的推荐报告
        """
        print("=" * 50)
        print("KOL 达人推荐系统启动")
        print("=" * 50)

        # 步骤 1: 读取用户需求
        self._step1_parse_demand(demand_input)

        # 步骤 2: 加载数据并初步筛选
        self._step2_filter_candidates()

        if self.candidates.empty:
            return "未找到符合条件的达人，请放宽筛选条件。"

        print(f"初步筛选: {len(self.candidates)} 个候选达人")

        # 步骤 3: 计算受众匹配度
        self._step3_match_audience()

        # 步骤 4: 计算性价比得分
        self.candidates = ValueScorer.score(self.candidates)
        print("性价比评分完成")

        # 步骤 5: 评估风险等级
        self.candidates = RiskAssessor.assess_batch(self.candidates)
        print("风险评估完成")

        # 步骤 6: 综合评分排序
        match_scores = dict(zip(self.candidates["kol_id"], self.candidates["match_score"]))
        self.candidates = CompositeScorer.compute(self.candidates, match_scores)
        print("综合评分完成")

        # 步骤 7: 筛选 TOP 10
        self.top10 = Ranker.top_n(self.candidates)
        print(f"TOP 10 筛选完成")

        # 步骤 8: 生成推荐理由
        self._step8_generate_reasons()

        # 步骤 9: 计算预估 ROI
        self._step9_compute_roi()

        # 步骤 10: 生成投放建议
        advice = self._step10_generate_advice()

        # 步骤 11: 格式化输出
        report = OutputFormatter.to_markdown(self.top10, advice)
        print("=" * 50)
        print("推荐报告生成完毕")
        print("=" * 50)

        return report

    def _step1_parse_demand(self, demand_input: dict | str):
        """步骤1: 解析需求"""
        if isinstance(demand_input, dict):
            self.demand = DemandParser.parse(demand_input)
        else:
            self.demand = DemandParser.parse_from_text(str(demand_input))
        print(f"需求解析: {self.demand.target_audience} | {self.demand.content_field} | {self.demand.budget_min}-{self.demand.budget_max}元")

    def _step2_filter_candidates(self):
        """步骤2: 加载数据并筛选"""
        loader = CSVLoader(self.csv_path)
        self.data = loader.load()
        ok, errs = loader.validate(self.data)
        if not ok:
            raise ValueError(f"数据验证失败: {errs}")
        self.candidates = CandidateFilter.filter(self.data, self.demand)

    def _step3_match_audience(self):
        """步骤3: 计算受众匹配度"""
        matcher = AudienceMatcher(llm_client=self.llm_client if self.use_llm else None)
        scores = {}
        reasons = {}

        print("计算受众匹配度...")
        for _, row in self.candidates.iterrows():
            result = matcher.match(row["audience"], self.demand.target_audience)
            scores[row["kol_id"]] = result["score"]
            reasons[row["kol_id"]] = result["reason"]

        self.candidates["match_score"] = self.candidates["kol_id"].map(scores)
        self.candidates["match_reason"] = self.candidates["kol_id"].map(reasons)
        print("受众匹配度计算完成")

    def _step8_generate_reasons(self):
        """步骤8: 生成推荐理由"""
        print("生成推荐理由...")
        reasons = []

        for _, row in self.top10.iterrows():
            if self.use_llm and self.llm_client:
                try:
                    reason = self.llm_client.generate_reason(
                        kol_name=row["kol_name"],
                        platform=row["platform"],
                        followers=int(row["followers"]),
                        price=int(row["price"]),
                        engagement_rate=float(row["engagement_rate"]),
                        conversion_rate=float(row["conversion_rate"]),
                        cooperation_count=int(row["cooperation_count"]),
                        audience_match_reason=row.get("match_reason", "受众匹配"),
                    )
                except Exception as e:
                    print(f"  [警告] {row['kol_name']} 推荐理由生成失败: {e}")
                    reason = self._fallback_reason(row)
            else:
                reason = self._fallback_reason(row)
            reasons.append(reason)

        self.top10["recommend_reason"] = reasons
        print("推荐理由生成完成")

    def _step9_compute_roi(self):
        """步骤9: 计算预估 ROI"""
        self.top10["roi"] = self.top10.apply(
            lambda row: ROICalculator.compute(row["conversion_rate"], row["price"]),
            axis=1,
        )
        print("ROI 计算完成")

    def _step10_generate_advice(self) -> str:
        """步骤10: 生成投放建议"""
        total_budget = self.demand.budget_max * 5  # 假设选5个达人
        platform_dist = self.top10["platform"].value_counts().to_dict()
        top_kols = self.top10[["kol_name", "platform", "followers", "price", "total_score"]].to_dict("records")

        if self.use_llm and self.llm_client:
            try:
                advice = self.llm_client.generate_advice(top_kols, total_budget, platform_dist)
            except Exception as e:
                print(f"[警告] 投放建议生成失败: {e}")
                advice = self._fallback_advice()
        else:
            advice = self._fallback_advice()

        print("投放建议生成完成")
        return advice

    @staticmethod
    def _fallback_reason(row) -> str:
        """推荐理由降级（无 LLM 时使用）"""
        parts = []
        match_score = row.get("match_score", 50)
        if match_score >= 80:
            parts.append("受众高度匹配")
        elif match_score >= 60:
            parts.append("受众部分匹配")
        else:
            parts.append("受众有一定重合")

        er = row["engagement_rate"]
        if er >= 4.0:
            parts.append(f"互动率{er}%优秀")
        else:
            parts.append(f"互动率{er}%良好")

        cr = row["conversion_rate"]
        parts.append(f"转化率{cr}%")

        cc = row["cooperation_count"]
        if cc >= 30:
            parts.append(f"合作{cc}次经验丰富")
        else:
            parts.append(f"合作{cc}次")

        return "，".join(parts)

    @staticmethod
    def _fallback_advice() -> str:
        """投放建议降级（无 LLM 时使用）"""
        return (
            "**预算分配建议：**\n"
            "- 建议选择 3-5 个达人组合投放，分散风险\n"
            "- 优先选择排名前 3 的高匹配度达人（占预算 60%）\n"
            "- 预留 20-30% 预算测试新达人\n\n"
            "**平台组合建议：**\n"
            "- 小红书：适合图文种草，用户决策周期短，转化率高\n"
            "- 抖音：适合短视频展示，传播范围广，适合品牌曝光\n"
            "- B站：用户粘性强，适合深度内容\n\n"
            "**注意事项：**\n"
            "1. 建议要求原创内容，避免硬广\n"
            "2. 首次合作建议签订详细合作协议\n"
            "3. 投放后建议追踪转化数据"
        )


if __name__ == "__main__":
    # 端到端测试
    pipeline = KOLPipeline(use_llm=True)

    form_data = {
        "target_audience": "大学生和应届生",
        "content_field": "校园",
        "budget_range": "1000-3000",
        "platforms": "小红书,抖音,B站,微博",
        "engagement_rate_min": "3.5",
    }

    report = pipeline.run(form_data)
    print("\n" + report)
