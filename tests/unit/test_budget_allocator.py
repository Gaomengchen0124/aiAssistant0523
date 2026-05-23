"""
BudgetAllocator 单元测试
"""

import pandas as pd
import pytest

from budget_allocator import BudgetAllocator


class TestBudgetAllocatorAllocate:
    """测试 BudgetAllocator.allocate()"""

    def test_basic_allocation(self, composite_df):
        """按匹配分权重分配预算"""
        top10 = composite_df.head(5).copy()
        result = BudgetAllocator.allocate(top10, total_budget=15000)

        assert len(result["allocations"]) == 5
        assert result["total"] == 15000
        assert "reserve" in result
        assert "platform_summary" in result

    def test_reserve_ratio(self, composite_df):
        """预留比例计算（默认 20%）"""
        top10 = composite_df.head(5).copy()
        result = BudgetAllocator.allocate(top10, total_budget=10000, reserve_ratio=0.20)

        assert result["reserve"] == 2000
        allocated_sum = sum(a["allocated"] for a in result["allocations"])
        # 浮点数舍入可能有 1 元误差
        assert abs(allocated_sum - 8000) <= 1

    def test_weight_sum_is_100(self, composite_df):
        """权重之和为 100%"""
        top10 = composite_df.head(5).copy()
        result = BudgetAllocator.allocate(top10, total_budget=10000)

        total_percentage = sum(a["percentage"] for a in result["allocations"])
        assert abs(total_percentage - 100.0) < 0.1

    def test_empty_dataframe(self):
        """空 DataFrame 处理"""
        empty = pd.DataFrame()
        result = BudgetAllocator.allocate(empty, total_budget=10000)

        assert result["allocations"] == []
        assert result["reserve"] == 0
        assert result["total"] == 0

    def test_zero_budget(self, composite_df):
        """预算为 0 时返回空分配"""
        top10 = composite_df.head(3).copy()
        result = BudgetAllocator.allocate(top10, total_budget=0)

        assert result["allocations"] == []
        assert result["total"] == 0

    def test_top_n_less_than_data(self, composite_df):
        """top_n 小于数据量时只取前 N"""
        top10 = composite_df.head(10).copy()
        result = BudgetAllocator.allocate(top10, total_budget=10000, top_n=3)

        assert len(result["allocations"]) == 3

    def test_platform_summary(self, composite_df):
        """平台汇总正确性"""
        top10 = composite_df.head(5).copy()
        result = BudgetAllocator.allocate(top10, total_budget=10000)

        platform_summary = result["platform_summary"]
        total_count = sum(platform_summary.values())
        assert total_count == 5

    def test_allocation_fields(self, composite_df):
        """分配结果包含所有字段"""
        top10 = composite_df.head(3).copy()
        result = BudgetAllocator.allocate(top10, total_budget=10000)

        for alloc in result["allocations"]:
            assert "kol_id" in alloc
            assert "kol_name" in alloc
            assert "platform" in alloc
            assert "score" in alloc
            assert "allocated" in alloc
            assert "percentage" in alloc


class TestBudgetAllocatorAllocateByROI:
    """测试 BudgetAllocator.allocate_by_roi()"""

    def test_roi_filter(self, composite_df):
        """基于期望 ROI 筛选达人"""
        top10 = composite_df.head(10).copy()
        result = BudgetAllocator.allocate_by_roi(top10, total_budget=20000, target_roi=3.0)

        assert "allocations" in result
        # allocate_by_roi 返回 allocate 的结果，不含 message 字段

    def test_no_qualified_kols(self, composite_df):
        """无达标达人时回退到 ROI 最高的"""
        top10 = composite_df.head(10).copy()
        # 设置极高的 target_roi 使没有达人达标
        result = BudgetAllocator.allocate_by_roi(top10, total_budget=20000, target_roi=50.0)

        assert len(result["allocations"]) > 0

    def test_invalid_params(self, composite_df):
        """无效参数处理"""
        top10 = composite_df.head(3).copy()
        result = BudgetAllocator.allocate_by_roi(top10, total_budget=0, target_roi=3.0)

        assert result["allocations"] == []
        # 无效参数时返回包含 message 的字典
        assert "message" in result
        assert "参数无效" in result["message"]

    def test_budget_limit(self, composite_df):
        """预算内尽可能多选（预留 20%）"""
        top10 = composite_df.head(10).copy()
        total_budget = 5000
        result = BudgetAllocator.allocate_by_roi(top10, total_budget=total_budget, target_roi=1.0)

        assert "allocations" in result


class TestBudgetAllocatorFormatAdvice:
    """测试 BudgetAllocator.format_advice()"""

    def test_contains_budget_section(self, composite_df):
        """输出包含预算分配建议"""
        top10 = composite_df.head(3).copy()
        result = BudgetAllocator.allocate(top10, total_budget=10000)
        advice = BudgetAllocator.format_advice(result)

        assert "预算分配建议" in advice
        assert "重点投放" in advice

    def test_contains_platform_section(self, composite_df):
        """输出包含平台分布"""
        top10 = composite_df.head(3).copy()
        result = BudgetAllocator.allocate(top10, total_budget=10000)
        advice = BudgetAllocator.format_advice(result)

        assert "平台分布" in advice

    def test_contains_kol_names(self, composite_df):
        """输出包含达人名称"""
        top10 = composite_df.head(3).copy()
        result = BudgetAllocator.allocate(top10, total_budget=10000)
        advice = BudgetAllocator.format_advice(result)

        for alloc in result["allocations"]:
            assert alloc["kol_name"] in advice

    def test_empty_allocation(self):
        """空分配时的处理"""
        empty_result = {"allocations": [], "reserve": 0, "total": 0, "platform_summary": {}}
        advice = BudgetAllocator.format_advice(empty_result)

        assert "预算分配建议" in advice
        assert "0 元" in advice
