"""
ROICalculator 单元测试
"""

import pytest

from roi_calculator import ROICalculator


class TestROICalculatorCompute:
    """测试 ROICalculator.compute()"""

    def test_basic_formula(self):
        """ROI 公式验证"""
        # ROI = (conversion_rate / 100 * 100 * 1000) / price
        # 3.5 / 100 * 100 * 1000 / 1200 = 3500 / 1200 ≈ 2.917
        result = ROICalculator.compute(3.5, 1200)
        assert result == "1:2.9"

    def test_price_zero(self):
        """price <= 0 时返回 1:0"""
        assert ROICalculator.compute(3.5, 0) == "1:0"
        assert ROICalculator.compute(3.5, -100) == "1:0"

    def test_roi_lower_bound(self):
        """ROI 值下限为 0.1"""
        # 极高的 price 会导致 ROI < 0.1
        result = ROICalculator.compute(0.1, 100000)
        assert float(result.split(":")[1]) >= 0.1

    def test_roi_upper_bound(self):
        """ROI 值上限为 10.0"""
        # 极高的 conversion_rate 会导致 ROI > 10
        result = ROICalculator.compute(50.0, 100)
        assert float(result.split(":")[1]) <= 10.0

    def test_return_format(self):
        """返回格式为 1:X.X"""
        result = ROICalculator.compute(3.5, 1200)
        assert result.startswith("1:")
        parts = result.split(":")
        assert len(parts) == 2
        assert float(parts[1]) >= 0

    def test_custom_conversion_value(self):
        """自定义转化价值"""
        result = ROICalculator.compute(3.5, 1200, conversion_value=200)
        # (3.5/100 * 200 * 1000) / 1200 = 7000/1200 ≈ 5.833
        assert result == "1:5.8"

    def test_compute_batch(self):
        """批量计算 ROI"""
        kols = [
            {"conversion_rate": 3.5, "price": 1200},
            {"conversion_rate": 4.1, "price": 3500},
        ]
        results = ROICalculator.compute_batch(kols)

        assert len(results) == 2
        assert "roi" in results[0]
        assert results[0]["roi"] == "1:2.9"
        assert results[1]["roi"] == "1:1.2"

    def test_compute_batch_preserves_original(self):
        """批量计算保留原始字段"""
        kols = [
            {"conversion_rate": 3.5, "price": 1200, "name": "达人A"},
        ]
        results = ROICalculator.compute_batch(kols)
        assert results[0]["name"] == "达人A"
        assert results[0]["conversion_rate"] == 3.5

    def test_compute_batch_default_values(self):
        """批量计算使用默认值处理缺失字段（conversion_rate=0 时 ROI 下限 0.1）"""
        kols = [
            {"price": 1200},  # 缺少 conversion_rate，默认 0
        ]
        results = ROICalculator.compute_batch(kols)
        assert "roi" in results[0]
        # conversion_rate=0 时 roi_value=0，但会被限制到最小 0.1
        assert results[0]["roi"] == "1:0.1"
