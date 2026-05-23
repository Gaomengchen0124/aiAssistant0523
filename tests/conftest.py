"""
pytest 共享 fixture
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# 将 src 加入路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from csv_loader import CSVLoader
from filters import CandidateFilter, Demand, DemandParser
import sys
sys.path.insert(0, str(Path(__file__).parent / "fixtures"))
from mock_llm import MockLLMClient
from pipeline import KOLPipeline
from scoring import CompositeScorer, RiskAssessor, ValueScorer


@pytest.fixture
def test_csv_path():
    """测试用 CSV 文件路径"""
    return str(Path(__file__).parent / "fixtures" / "test_influencers.csv")


@pytest.fixture
def sample_df(test_csv_path):
    """加载测试用 DataFrame"""
    loader = CSVLoader(test_csv_path)
    df = loader.load()
    return df


@pytest.fixture
def sample_demand():
    """标准测试需求对象"""
    return DemandParser.parse({
        "target_audience": "大学生和应届生",
        "content_field": "校园",
        "budget_range": "1000-3000",
        "platforms": "小红书,抖音,B站,微博",
        "engagement_rate_min": "3.0",
    })


@pytest.fixture
def mock_llm_client():
    """Mock LLM 客户端"""
    return MockLLMClient()


@pytest.fixture
def candidates_df(sample_df, sample_demand):
    """经过初步筛选后的候选达人 DataFrame"""
    return CandidateFilter.filter(sample_df, sample_demand)


@pytest.fixture
def scored_df(candidates_df):
    """经过性价比评分的 DataFrame"""
    df = ValueScorer.score(candidates_df)
    df = RiskAssessor.assess_batch(df)
    # 添加模拟的受众匹配分
    df["match_score"] = 85.0
    return df


@pytest.fixture
def composite_df(scored_df):
    """经过综合评分的 DataFrame"""
    match_scores = dict(zip(scored_df["kol_id"], scored_df["match_score"]))
    return CompositeScorer.compute(scored_df, match_scores)


@pytest.fixture
def mock_pipeline(test_csv_path, mock_llm_client, monkeypatch):
    """使用 Mock LLM 的 KOLPipeline 实例"""
    # 使用 monkeypatch 替换 LLMClient
    import llm_client
    original_llm_client = llm_client.LLMClient
    monkeypatch.setattr(llm_client, "LLMClient", MockLLMClient)

    pipeline = KOLPipeline(csv_path=test_csv_path, use_llm=True)
    # 直接替换 pipeline 中的 llm_client 为 mock
    pipeline.llm_client = mock_llm_client
    return pipeline


@pytest.fixture
def sample_form_data():
    """标准表单输入数据"""
    return {
        "target_audience": "大学生和应届生",
        "content_field": "校园",
        "budget_range": "1000-3000",
        "platforms": "小红书,抖音,B站,微博",
        "engagement_rate_min": "3.0",
    }


@pytest.fixture
def minimal_form_data():
    """最小必填表单数据"""
    return {
        "target_audience": "大学生",
        "content_field": "校园",
        "budget_range": "1000-3000",
        "platforms": "小红书",
    }
