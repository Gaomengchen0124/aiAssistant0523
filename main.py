"""
KOL 达人推荐系统 - CLI 入口
"""

import sys
from pathlib import Path

# 将 src 加入路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pipeline import KOLPipeline


def main():
    print("=" * 60)
    print("   AI KOL / 达人匹配助手")
    print("=" * 60)

    # 交互式输入
    print("\n请填写投放需求（直接回车使用默认值）：\n")

    target_audience = input("目标受众（默认：大学生和应届生）：").strip() or "大学生和应届生"
    content_field = input("内容领域（默认：校园）：").strip() or "校园"
    budget_range = input("预算范围（默认：1000-3000元）：").strip() or "1000-3000"
    platforms = input("投放平台（默认：小红书,抖音,B站,微博）：").strip() or "小红书,抖音,B站,微博"

    engagement_rate_min = input("最低互动率%（默认：3.0）：").strip() or "3.0"

    form_data = {
        "target_audience": target_audience,
        "content_field": content_field,
        "budget_range": budget_range,
        "platforms": platforms,
        "engagement_rate_min": engagement_rate_min,
    }

    print("\n" + "=" * 60)
    print("开始分析...")
    print("=" * 60 + "\n")

    pipeline = KOLPipeline(use_llm=True)
    report = pipeline.run(form_data)

    print("\n" + report)


if __name__ == "__main__":
    main()
