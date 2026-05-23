"""
LLM 调用封装（DeepSeek，兼容 OpenAI SDK）
"""

import os
import time
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LLMClient:
    """封装 LLM 请求：受众匹配度、推荐理由、投放建议"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
        timeout: int = None,
        max_retries: int = None,
    ):
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
        self.model = model or os.getenv("LLM_MODEL", "deepseek-chat")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", "60"))
        self.max_retries = max_retries or int(os.getenv("LLM_MAX_RETRIES", "3"))

        if not self.api_key:
            raise ValueError("LLM_API_KEY 未设置，请在 .env 文件中配置")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    def _chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """通用聊天接口"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()

    def match_audience(self, audience_text: str, target_audience: str) -> dict:
        """
        受众匹配度评估

        Returns:
            {"score": float(0-100), "reason": str}
        """
        system_prompt = (
            "你是一位专业的营销数据分析师。请评估达人受众画像与品牌目标受众的匹配程度。"
            "输出格式必须是：分数|理由\n分数为0-100之间的整数，理由在30字以内。"
        )
        user_prompt = f"达人受众画像：{audience_text}\n品牌目标受众：{target_audience}"

        result = self._chat(system_prompt, user_prompt, temperature=0.2)
        try:
            score_str, reason = result.split("|", 1)
            score = float(score_str.strip())
            score = max(0, min(100, score))
        except (ValueError, IndexError):
            # 解析失败时回退
            score = 50.0
            reason = "受众匹配度评估中"

        return {"score": score, "reason": reason.strip()}

    def generate_reason(
        self,
        kol_name: str,
        platform: str,
        followers: int,
        price: int,
        engagement_rate: float,
        conversion_rate: float,
        cooperation_count: int,
        audience_match_reason: str,
    ) -> str:
        """
        生成推荐理由（50-100字）
        """
        system_prompt = (
            "你是一位资深的 KOL 投放顾问。请根据达人数据生成一段简洁有力的推荐理由，"
            "50-100字，必须包含具体数据支撑。"
        )
        user_prompt = (
            f"达人：{kol_name}（{platform}，{followers}粉）\n"
            f"报价：{price}元，互动率：{engagement_rate}%，转化率：{conversion_rate}%\n"
            f"合作次数：{cooperation_count}次\n"
            f"受众匹配：{audience_match_reason}\n"
            f"请生成推荐理由。"
        )
        return self._chat(system_prompt, user_prompt, temperature=0.5)

    def generate_advice(
        self,
        top_kols: list[dict],
        total_budget: int,
        platform_distribution: dict[str, int],
    ) -> str:
        """
        生成投放建议（200-300字）
        """
        system_prompt = (
            "你是一位资深的社交媒体投放策略师。请根据推荐的达人列表生成投放建议，"
            "包含预算分配、平台组合、注意事项三部分，200-300字。"
        )

        kol_summary = "\n".join(
            f"- {k['kol_name']}（{k['platform']}，{k['followers']}粉，报价{k['price']}元，匹配分{k.get('total_score', 0):.0f}）"
            for k in top_kols[:5]
        )

        platform_summary = ", ".join(
            f"{p}（{c}人）" for p, c in platform_distribution.items()
        )

        user_prompt = (
            f"推荐达人 TOP5：\n{kol_summary}\n\n"
            f"总预算：{total_budget}元\n"
            f"平台分布：{platform_summary}\n\n"
            f"请生成投放建议。"
        )
        return self._chat(system_prompt, user_prompt, temperature=0.5)

    def parse_demand_text(self, text: str) -> dict:
        """
        从自由文本中解析结构化投放需求

        Args:
            text: 用户输入的自由文本，如产品策划案或需求描述

        Returns:
            {
                "gender": str,
                "age_min": int,
                "age_max": int,
                "occupation": str,
                "content_field": str,
                "budget_min": int,
                "budget_max": int,
                "platforms": list[str],
                "engagement_rate_min": float,
                "conversion_rate_min": float,
                "risk_preference": str,
                "confidence": float,
            }
        """
        system_prompt = (
            "你是一位需求分析师，擅长从用户的自由文本中提取结构化的投放需求信息。"
            "请从以下文本中提取关键信息，并以 JSON 格式返回。"
            "如果某项信息无法从文本中推断，请返回 null。"
            "返回格式必须是合法的 JSON，不要包含任何其他文字。"
        )

        user_prompt = (
            f"请分析以下投放需求文本，提取结构化信息：\n\n{text}\n\n"
            "请返回以下字段的 JSON 格式：\n"
            '{\n'
            '  "gender": "性别：男/女/不限，推断不出则 null",\n'
            '  "age_min": "目标年龄下限，数字，推断不出则 null",\n'
            '  "age_max": "目标年龄上限，数字，推断不出则 null",\n'
            '  "occupation": "职业或身份描述，如大学生、职场新人、宝妈等，推断不出则 null",\n'
            '  "content_field": "内容领域，如校园、职场、美妆、科技、美食、旅游、健身、母婴，推断不出则 null",\n'
            '  "budget_min": "预算下限（元），数字，推断不出则 null",\n'
            '  "budget_max": "预算上限（元），数字，推断不出则 null",\n'
            '  "platforms": ["投放平台列表，如小红书、抖音、B站、微博，推断不出则 []"],\n'
            '  "engagement_rate_min": "最低互动率要求（%），数字，推断不出则 null",\n'
            '  "conversion_rate_min": "最低转化率要求（%），数字，推断不出则 null",\n'
            '  "risk_preference": "风险偏好：保守/平衡/激进，推断不出则 null",\n'
            '  "total_budget": "总预算（元），数字，推断不出则 null",\n'
            '  "num_kols": "期望合作达人数量，数字，推断不出则 null",\n'
            '  "target_roi": "期望ROI（如 1:3 则返回 3.0），数字，推断不出则 null",\n'
            '  "confidence": "信息完整度置信度（0-1），数字"\n'
            '}'
        )

        result = self._chat(system_prompt, user_prompt, temperature=0.3)

        # 尝试解析 JSON
        import json as json_mod
        try:
            # 清理可能的 markdown 代码块
            cleaned = result.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            data = json_mod.loads(cleaned)
            # 确保 confidence 字段存在
            if "confidence" not in data:
                data["confidence"] = 0.5
            return data
        except (json_mod.JSONDecodeError, ValueError):
            # 解析失败时返回空结构
            return {
                "gender": None, "age_min": None, "age_max": None,
                "occupation": None, "content_field": None,
                "budget_min": None, "budget_max": None,
                "platforms": [], "engagement_rate_min": None,
                "conversion_rate_min": None, "risk_preference": None,
                "total_budget": None, "num_kols": None, "target_roi": None,
                "confidence": 0.0,
            }


if __name__ == "__main__":
    # 连通性测试
    client = LLMClient()
    print("LLM 客户端初始化成功")

    # 测试受众匹配
    result = client.match_audience("大学生、应届生、18-25岁", "大学生和应届生")
    print(f"\n受众匹配测试：{result}")

    # 测试推荐理由
    reason = client.generate_reason(
        kol_name="校园成长Ada",
        platform="小红书",
        followers=50000,
        price=1200,
        engagement_rate=3.8,
        conversion_rate=3.5,
        cooperation_count=15,
        audience_match_reason="受众高度匹配，大学生占比85%",
    )
    print(f"\n推荐理由测试：{reason}")
