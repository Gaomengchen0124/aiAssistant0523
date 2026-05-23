"""
ROI 预估计算
"""


class ROICalculator:
    """基于历史转化率和报价计算预估 ROI"""

    # 假设每次转化的价值（元），用于简化计算
    DEFAULT_CONVERSION_VALUE = 100

    @staticmethod
    def compute(conversion_rate: float, price: float, conversion_value: float = None) -> str:
        """
        计算预估 ROI

        Args:
            conversion_rate: 历史转化率（百分比，如 3.5）
            price: 合作报价（元）
            conversion_value: 单次转化价值（元），默认 100

        Returns:
            ROI 字符串，如 "1:2.9"
        """
        if conversion_value is None:
            conversion_value = ROICalculator.DEFAULT_CONVERSION_VALUE

        if price <= 0:
            return "1:0"

        # ROI = (转化率% × 转化价值 × 1000次曝光) / 报价
        # 简化为: (转化率 / 100 × 转化价值 × 1000) / 报价
        # 或者直接用公式: 转化率对应的回报倍数
        roi_value = (conversion_rate / 100 * conversion_value * 1000) / price

        # 限制在合理范围 1:0 到 1:10
        roi_value = max(0.1, min(roi_value, 10.0))

        return f"1:{roi_value:.1f}"

    @staticmethod
    def compute_batch(kols: list[dict]) -> list[dict]:
        """批量计算 ROI，为每个达人添加 roi 字段"""
        results = []
        for kol in kols:
            roi = ROICalculator.compute(
                conversion_rate=kol.get("conversion_rate", 0),
                price=kol.get("price", 1),
            )
            kol_copy = dict(kol)
            kol_copy["roi"] = roi
            results.append(kol_copy)
        return results


if __name__ == "__main__":
    # 测试
    print(ROICalculator.compute(3.5, 1200))  # 预期约 1:2.9
    print(ROICalculator.compute(4.1, 3500))  # 预期约 1:1.2
    print(ROICalculator.compute(3.8, 2800))  # 预期约 1:1.4
