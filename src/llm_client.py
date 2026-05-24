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
            "你是一位专业的营销需求分析师，擅长从用户的产品描述和投放需求中提取结构化的投放参数。"
            "请严格按以下规则提取，不要猜测用户没有明确提到的信息。"
            "返回格式必须是合法的 JSON，不要包含任何其他文字。"
        )

        user_prompt = (
            f"请分析以下投放需求文本，提取结构化信息：\n\n{text}\n\n"
            "=== 字段定义与提取规则 ===\n"
            "1. gender: 性别偏好。只能从文本中明确提到的推断，未提及则 null。\n"
            "2. age_min / age_max: 年龄范围。根据受众身份推断，多场景时取覆盖最广的范围。"
            "例如'大学生'→18-24，'职场新人'→22-28，'宝妈'→25-35。"
            "如果同时提到多个场景（如'校园、办公'），取并集范围，不要只取最窄的。\n"
            "3. occupation: 目标受众的职业或身份。如'大学生''白领''宝妈'。"
            "注意区分：'校园''职场'是场景/内容领域，不是受众身份。"
            "多个场景的受众用顿号连接，如'学生、白领'。\n"
            "4. content_field: 内容领域/产品类别。根据产品关键词推断："
            "'鼠标''耳机''手机'→'数码'，'护肤品''口红'→'美妆'，'课程''培训'→'教育'，"
            "'母婴用品'→'母婴'，'零食''饮料'→'美食'。"
            "如果产品不明确，根据场景推断（如'校园推广'→'校园'）。\n"
            "5. platforms: 投放平台列表。只提取明确提到的平台名称。\n"
            "6. target_roi: 期望 ROI。提取文本中 ROI 相关的数字。"
            "如'ROI 1:3''回报 1:3''roi为1：3'均提取为 3.0。\n"
            "7. total_budget: 总预算。提取明确提到的金额数字。\n"
            "8. confidence: 信息完整度（0-1）。提取越完整、推断依据越明确，分数越高。\n\n"
            "=== 示例 ===\n"
            "输入：'推广一款考研英语课程，面向大三学生，预算2万，主要投小红书'\n"
            '输出：{"gender": "不限", "age_min": 20, "age_max": 23, "occupation": "大学生", '
            '"content_field": "教育", "budget_min": null, "budget_max": null, "platforms": ["小红书"], '
            '"total_budget": 20000, "target_roi": null, "confidence": 0.85}\n\n'
            "输入：'一款静音鼠标的产品宣发，服务校园、办公场景，希望roi为1：3，优先选择小红书和抖音'\n"
            '输出：{"gender": "不限", "age_min": 18, "age_max": 35, "occupation": "学生、白领", '
            '"content_field": "数码", "budget_min": null, "budget_max": null, "platforms": ["小红书", "抖音"], '
            '"total_budget": null, "target_roi": 3.0, "confidence": 0.75}\n\n'
            "请返回以下字段的 JSON 格式：\n"
            '{\n'
            '  "gender": ...,\n'
            '  "age_min": ...,\n'
            '  "age_max": ...,\n'
            '  "occupation": ...,\n'
            '  "content_field": ...,\n'
            '  "budget_min": ...,\n'
            '  "budget_max": ...,\n'
            '  "platforms": [...],\n'
            '  "engagement_rate_min": ...,\n'
            '  "conversion_rate_min": ...,\n'
            '  "risk_preference": ...,\n'
            '  "total_budget": ...,\n'
            '  "num_kols": ...,\n'
            '  "target_roi": ...,\n'
            '  "confidence": ...\n'
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
