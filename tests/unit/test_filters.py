"""
DemandParser + CandidateFilter 单元测试
"""

import pandas as pd
import pytest

from filters import CandidateFilter, Demand, DemandParser


class TestDemandParserParse:
    """测试 DemandParser.parse()"""

    def test_parse_valid_form(self):
        """正常解析表单数据"""
        form = {
            "target_audience": "大学生和应届生",
            "content_field": "校园",
            "budget_range": "1000-3000",
            "platforms": "小红书,抖音",
            "engagement_rate_min": "3.5",
        }
        demand = DemandParser.parse(form)

        assert isinstance(demand, Demand)
        assert demand.target_audience == "大学生和应届生"
        assert demand.content_field == "校园"
        assert demand.budget_min == 1000
        assert demand.budget_max == 3000
        assert demand.platforms == ["小红书", "抖音"]
        assert demand.engagement_rate_min == 3.5

    def test_parse_missing_required_field(self):
        """必填字段缺失时抛出 ValueError"""
        with pytest.raises(ValueError, match="必填字段不完整"):
            DemandParser.parse({
                "target_audience": "大学生",
                "content_field": "",
                "budget_range": "1000-3000",
                "platforms": "小红书",
            })

    def test_parse_budget_formats(self):
        """各种预算字符串格式"""
        cases = [
            ("1000-3000", 1000, 3000),
            ("1000~3000", 1000, 3000),
            ("500-50000", 500, 50000),
            ("2000元-4000元", 2000, 4000),
        ]
        for budget_str, expected_min, expected_max in cases:
            form = {
                "target_audience": "大学生",
                "content_field": "校园",
                "budget_range": budget_str,
                "platforms": "小红书",
            }
            demand = DemandParser.parse(form)
            assert demand.budget_min == expected_min, f"预算 {budget_str} 解析失败"
            assert demand.budget_max == expected_max, f"预算 {budget_str} 解析失败"

    def test_parse_invalid_budget_too_low(self):
        """预算下限 < 500 时抛出 ValueError"""
        with pytest.raises(ValueError, match="预算范围不合理"):
            DemandParser.parse({
                "target_audience": "大学生",
                "content_field": "校园",
                "budget_range": "300-3000",
                "platforms": "小红书",
            })

    def test_parse_invalid_budget_too_high(self):
        """预算上限 > 50000 时抛出 ValueError"""
        with pytest.raises(ValueError, match="预算范围不合理"):
            DemandParser.parse({
                "target_audience": "大学生",
                "content_field": "校园",
                "budget_range": "1000-60000",
                "platforms": "小红书",
            })

    def test_parse_invalid_budget_min_gte_max(self):
        """下限 >= 上限时抛出 ValueError"""
        with pytest.raises(ValueError, match="预算范围不合理"):
            DemandParser.parse({
                "target_audience": "大学生",
                "content_field": "校园",
                "budget_range": "3000-1000",
                "platforms": "小红书",
            })

    def test_parse_platform_separators(self):
        """平台解析：逗号/斜杠分隔"""
        cases = [
            ("小红书,抖音", ["小红书", "抖音"]),
            ("小红书/抖音/B站", ["小红书", "抖音", "B站"]),
            ("小红书, 抖音, B站", ["小红书", "抖音", "B站"]),
        ]
        for platform_str, expected in cases:
            form = {
                "target_audience": "大学生",
                "content_field": "校园",
                "budget_range": "1000-3000",
                "platforms": platform_str,
            }
            demand = DemandParser.parse(form)
            assert demand.platforms == expected, f"平台 '{platform_str}' 解析失败"

    def test_parse_no_platform(self):
        """未选择平台时抛出 ValueError（必填字段不完整）"""
        with pytest.raises(ValueError, match="必填字段不完整"):
            DemandParser.parse({
                "target_audience": "大学生",
                "content_field": "校园",
                "budget_range": "1000-3000",
                "platforms": "",
            })

    def test_parse_optional_fields(self):
        """可选字段解析"""
        form = {
            "target_audience": "大学生",
            "content_field": "校园",
            "budget_range": "1000-3000",
            "platforms": "小红书",
            "followers_range": "5万-20万",
            "engagement_rate_min": "3.5",
            "conversion_rate_min": "2.0",
        }
        demand = DemandParser.parse(form)
        assert demand.followers_min == 50000
        assert demand.followers_max == 200000
        assert demand.engagement_rate_min == 3.5
        assert demand.conversion_rate_min == 2.0

    def test_parse_default_risk_preference(self):
        """风险偏好默认值"""
        form = {
            "target_audience": "大学生",
            "content_field": "校园",
            "budget_range": "1000-3000",
            "platforms": "小红书",
        }
        demand = DemandParser.parse(form)
        assert demand.risk_preference == "平衡"
        assert demand.cooperation_preference == "无偏好"


class TestDemandParserParseFromText:
    """测试 DemandParser.parse_from_text()"""

    def test_parse_from_text_basic(self):
        """从自然语言文本中提取关键信息"""
        text = "我们要找小红书达人，目标受众是大学生，预算1000-3000元，校园领域"
        demand = DemandParser.parse_from_text(text)

        assert "小红书" in demand.platforms
        assert demand.budget_min == 1000
        assert demand.budget_max == 3000
        assert demand.content_field == "校园"

    def test_parse_from_text_default_platforms(self):
        """文本中未提到平台时返回默认全部平台"""
        text = "我们要找达人，目标受众是大学生，预算1000-3000元"
        demand = DemandParser.parse_from_text(text)

        assert demand.platforms == ["小红书", "抖音", "B站", "微博"]


class TestDemandParserParseBudget:
    """测试 DemandParser._parse_budget()"""

    def test_parse_budget_dash(self):
        assert DemandParser._parse_budget("1000-3000") == (1000, 3000)

    def test_parse_budget_tilde(self):
        assert DemandParser._parse_budget("1000~3000") == (1000, 3000)

    def test_parse_budget_invalid_format(self):
        with pytest.raises(ValueError, match="预算范围格式错误"):
            DemandParser._parse_budget("invalid")

    def test_parse_budget_unreasonable(self):
        with pytest.raises(ValueError, match="预算范围不合理"):
            DemandParser._parse_budget("100-200")


class TestDemandParserParseFollowers:
    """测试 DemandParser._parse_followers()"""

    def test_parse_followers_wan(self):
        assert DemandParser._parse_followers("5万-20万") == (50000, 200000)

    def test_parse_followers_w(self):
        assert DemandParser._parse_followers("5w-20w") == (50000, 200000)

    def test_parse_followers_number(self):
        assert DemandParser._parse_followers("50000-200000") == (50000, 200000)

    def test_parse_followers_insufficient(self):
        """只有一个数字时返回 None"""
        assert DemandParser._parse_followers("5万") == (None, None)


class TestCandidateFilter:
    """测试 CandidateFilter.filter()"""

    def test_filter_by_platform(self, sample_df, sample_demand):
        """平台筛选正确性"""
        demand = DemandParser.parse({
            "target_audience": "大学生",
            "content_field": "校园",
            "budget_range": "1000-5000",
            "platforms": "小红书",
        })
        result = CandidateFilter.filter(sample_df, demand)

        assert all(result["platform"] == "小红书")
        assert len(result) < len(sample_df)

    def test_filter_by_budget(self, sample_df):
        """预算范围筛选"""
        demand = DemandParser.parse({
            "target_audience": "大学生",
            "content_field": "校园",
            "budget_range": "1000-2000",
            "platforms": "小红书,抖音,B站,微博",
        })
        result = CandidateFilter.filter(sample_df, demand)

        assert all(result["price"] >= 1000)
        assert all(result["price"] <= 2000)

    def test_filter_by_field(self, sample_df):
        """内容领域模糊匹配"""
        demand = DemandParser.parse({
            "target_audience": "大学生",
            "content_field": "校园",
            "budget_range": "1000-5000",
            "platforms": "小红书,抖音,B站,微博",
        })
        result = CandidateFilter.filter(sample_df, demand)

        assert len(result) > 0
        assert all(result["field"].str.contains("校园", case=False, na=False))

    def test_filter_by_engagement_rate(self, sample_df):
        """互动率筛选"""
        demand = DemandParser.parse({
            "target_audience": "大学生",
            "content_field": "校园",
            "budget_range": "1000-5000",
            "platforms": "小红书,抖音,B站,微博",
            "engagement_rate_min": "4.0",
        })
        result = CandidateFilter.filter(sample_df, demand)

        assert all(result["engagement_rate"] >= 4.0)

    def test_filter_no_match(self, sample_df):
        """无匹配结果时返回空 DataFrame"""
        demand = DemandParser.parse({
            "target_audience": "大学生",
            "content_field": "不存在领域",
            "budget_range": "1000-5000",
            "platforms": "小红书,抖音,B站,微博",
        })
        result = CandidateFilter.filter(sample_df, demand)

        assert result.empty

    def test_filter_by_followers(self, sample_df):
        """粉丝数筛选"""
        demand = DemandParser.parse({
            "target_audience": "大学生",
            "content_field": "校园",
            "budget_range": "1000-5000",
            "platforms": "小红书,抖音,B站,微博",
        })
        demand.followers_min = 100000
        result = CandidateFilter.filter(sample_df, demand)

        assert all(result["followers"] >= 100000)

    def test_filter_all_conditions(self, sample_df):
        """多条件组合筛选"""
        demand = DemandParser.parse({
            "target_audience": "大学生",
            "content_field": "校园",
            "budget_range": "1000-3000",
            "platforms": "小红书",
            "engagement_rate_min": "3.5",
        })
        result = CandidateFilter.filter(sample_df, demand)

        assert all(result["platform"] == "小红书")
        assert all(result["price"] >= 1000)
        assert all(result["price"] <= 3000)
        assert all(result["engagement_rate"] >= 3.5)
        assert all(result["field"].str.contains("校园", case=False, na=False))
