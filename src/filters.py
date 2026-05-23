"""
需求解析 + 初步筛选
"""

import re
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


@dataclass
class Demand:
    """结构化需求对象"""
    target_audience: str
    content_field: str
    budget_min: int
    budget_max: int
    platforms: list[str]
    followers_min: Optional[int] = None
    followers_max: Optional[int] = None
    engagement_rate_min: Optional[float] = None
    conversion_rate_min: Optional[float] = None
    risk_preference: str = "平衡"  # 保守/平衡/激进
    cooperation_preference: str = "无偏好"  # 优先新达人/优先老达人/无偏好


class DemandParser:
    """解析用户表单输入为结构化需求"""

    @staticmethod
    def parse(form_data: dict) -> Demand:
        """解析表单数据为 Demand 对象"""
        # 必填字段
        target_audience = form_data.get("target_audience", "").strip()
        content_field = form_data.get("content_field", "").strip()
        budget_range = form_data.get("budget_range", "").strip()
        platforms_str = form_data.get("platforms", "").strip()

        if not all([target_audience, content_field, budget_range, platforms_str]):
            raise ValueError("必填字段不完整：目标受众、内容领域、预算范围、投放平台")

        # 解析预算范围
        budget_min, budget_max = DemandParser._parse_budget(budget_range)

        # 解析平台（多选用 / 或 , 分隔）
        platforms = re.split(r"[,/\\s]+", platforms_str)
        platforms = [p.strip() for p in platforms if p.strip()]
        if not platforms:
            raise ValueError("至少选择一个投放平台")

        # 可选字段
        followers_min, followers_max = None, None
        if form_data.get("followers_range"):
            followers_min, followers_max = DemandParser._parse_followers(form_data["followers_range"])

        engagement_rate_min = None
        if form_data.get("engagement_rate_min"):
            engagement_rate_min = float(form_data["engagement_rate_min"])

        conversion_rate_min = None
        if form_data.get("conversion_rate_min"):
            conversion_rate_min = float(form_data["conversion_rate_min"])

        return Demand(
            target_audience=target_audience,
            content_field=content_field,
            budget_min=budget_min,
            budget_max=budget_max,
            platforms=platforms,
            followers_min=followers_min,
            followers_max=followers_max,
            engagement_rate_min=engagement_rate_min,
            conversion_rate_min=conversion_rate_min,
            risk_preference=form_data.get("risk_preference", "平衡"),
            cooperation_preference=form_data.get("cooperation_preference", "无偏好"),
        )

    @staticmethod
    def parse_from_text(text: str) -> Demand:
        """从自然语言文本中解析需求（简化版，提取关键信息）"""
        # 提取预算
        budget_pattern = r"(\d+)-(\d+)\s*元"
        budget_match = re.search(budget_pattern, text)
        if budget_match:
            budget_range = f"{budget_match.group(1)}-{budget_match.group(2)}"
        else:
            budget_range = "1000-5000"

        # 提取平台
        platforms = []
        platform_map = {"小红书": "小红书", "抖音": "抖音", "B站": "B站", "微博": "微博"}
        for keyword, platform in platform_map.items():
            if keyword in text:
                platforms.append(platform)
        if not platforms:
            platforms = ["小红书", "抖音", "B站", "微博"]

        # 提取领域（简单关键词匹配）
        field_keywords = ["校园", "职场", "美妆", "科技", "美食", "旅游", "健身", "母婴"]
        content_field = ""
        for kw in field_keywords:
            if kw in text:
                content_field = kw
                break
        if not content_field:
            content_field = "综合"

        return Demand(
            target_audience=text[:50],
            content_field=content_field,
            budget_min=int(budget_range.split("-")[0]),
            budget_max=int(budget_range.split("-")[1]),
            platforms=platforms,
        )

    @staticmethod
    def _parse_budget(budget_str: str) -> tuple[int, int]:
        """解析预算范围字符串，如 '1000-3000' 或 '1000~3000'"""
        nums = re.findall(r"\d+", budget_str.replace("~", "-"))
        if len(nums) < 2:
            raise ValueError(f"预算范围格式错误: {budget_str}，应为 '1000-3000'")
        min_val, max_val = int(nums[0]), int(nums[1])
        if min_val < 500 or max_val > 50000 or min_val >= max_val:
            raise ValueError(f"预算范围不合理: {min_val}-{max_val}")
        return min_val, max_val

    @staticmethod
    def _parse_followers(followers_str: str) -> tuple[Optional[int], Optional[int]]:
        """解析粉丝数范围，支持 '5万-20万' 或 '50000-200000'"""
        s = followers_str.replace("万", "0000").replace("w", "0000").replace("W", "0000")
        nums = re.findall(r"\d+", s)
        if len(nums) >= 2:
            return int(nums[0]), int(nums[1])
        return None, None


class CandidateFilter:
    """基于平台/领域/预算/粉丝数初步筛选达人"""

    @staticmethod
    def filter(df: pd.DataFrame, demand: Demand) -> pd.DataFrame:
        """硬过滤，返回候选达人列表"""
        candidates = df.copy()

        # 1. 平台筛选
        candidates = candidates[candidates["platform"].isin(demand.platforms)]

        # 2. 预算筛选
        candidates = candidates[
            (candidates["price"] >= demand.budget_min) &
            (candidates["price"] <= demand.budget_max)
        ]

        # 3. 内容领域筛选（模糊匹配）
        if demand.content_field:
            field_mask = candidates["field"].str.contains(
                demand.content_field, case=False, na=False
            )
            candidates = candidates[field_mask]

        # 4. 粉丝数筛选
        if demand.followers_min is not None:
            candidates = candidates[candidates["followers"] >= demand.followers_min]
        if demand.followers_max is not None:
            candidates = candidates[candidates["followers"] <= demand.followers_max]

        # 5. 互动率筛选
        if demand.engagement_rate_min is not None:
            candidates = candidates[candidates["engagement_rate"] >= demand.engagement_rate_min]

        # 6. 转化率筛选
        if demand.conversion_rate_min is not None:
            candidates = candidates[candidates["conversion_rate"] >= demand.conversion_rate_min]

        return candidates


if __name__ == "__main__":
    # 测试
    from csv_loader import CSVLoader

    loader = CSVLoader()
    df = loader.load()

    # 测试表单解析
    form = {
        "target_audience": "大学生和应届生",
        "content_field": "校园",
        "budget_range": "1000-3000",
        "platforms": "小红书,抖音",
        "engagement_rate_min": "3.5",
    }
    demand = DemandParser.parse(form)
    print(f"[OK] Demand parsed: {demand.content_field} | {demand.budget_min}-{demand.budget_max} | platforms={demand.platforms}")

    # 测试筛选
    candidates = CandidateFilter.filter(df, demand)
    print(f"[OK] Candidates after filter: {len(candidates)}")
    if not candidates.empty:
        print(candidates[["kol_name", "platform", "price", "engagement_rate"]].head().to_string(index=False))
    else:
        print("[WARN] No candidates matched")
