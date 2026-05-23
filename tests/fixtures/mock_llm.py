"""
LLMClient 的 Mock 实现，用于测试时避免真实 API 调用
"""


class MockLLMClient:
    """Mock LLMClient，返回固定值"""

    def __init__(self, *args, **kwargs):
        pass

    def match_audience(self, audience_text: str, target_audience: str) -> dict:
        """返回固定匹配分数"""
        score = 85.0
        return {"score": score, "reason": f"受众匹配度评估：{audience_text} 与 {target_audience} 高度匹配"}

    def generate_reason(self, **kwargs) -> str:
        """返回固定推荐理由"""
        kol_name = kwargs.get("kol_name", "未知达人")
        engagement_rate = kwargs.get("engagement_rate", 3.0)
        conversion_rate = kwargs.get("conversion_rate", 3.0)
        return (
            f"{kol_name}受众高度匹配，互动率{engagement_rate}%优秀，"
            f"转化率{conversion_rate}%高于平均水平，数据表现良好，推荐合作。"
        )

    def generate_advice(self, top_kols: list, total_budget: int, platform_distribution: dict) -> str:
        """返回固定投放建议"""
        return (
            "**预算分配建议：**\n"
            "- 建议选择 3-5 个达人组合投放，分散风险\n"
            "- 优先选择排名前 3 的高匹配度达人（占预算 60%）\n"
            "- 预留 20-30% 预算测试新达人\n\n"
            "**平台组合建议：**\n"
            "- 小红书：适合图文种草，用户决策周期短，转化率高\n"
            "- 抖音：适合短视频展示，传播范围广，适合品牌曝光\n\n"
            "**注意事项：**\n"
            "1. 建议要求原创内容，避免硬广\n"
            "2. 首次合作建议签订详细合作协议\n"
            "3. 投放后建议追踪转化数据"
        )

    def parse_demand_text(self, text: str) -> dict:
        """返回固定解析结果"""
        return {
            "gender": "不限",
            "age_min": 18,
            "age_max": 25,
            "occupation": "大学生",
            "content_field": "校园",
            "budget_min": 1000,
            "budget_max": 3000,
            "platforms": ["小红书", "抖音"],
            "engagement_rate_min": 3.0,
            "conversion_rate_min": None,
            "risk_preference": "平衡",
            "total_budget": 15000,
            "num_kols": 5,
            "target_roi": None,
            "confidence": 0.85,
        }
