"""
LLMClient 单元测试（无需真实 API 调用）
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from llm_client import LLMClient


class TestLLMClientInit:
    """测试 LLMClient 初始化"""

    def test_init_no_api_key(self, monkeypatch):
        """无 API key 时抛出 ValueError"""
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        with pytest.raises(ValueError, match="LLM_API_KEY"):
            LLMClient()

    def test_init_with_api_key(self, monkeypatch):
        """提供 API key 时正常初始化"""
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_BASE_URL", "https://test.example.com/v1")
        monkeypatch.setenv("LLM_MODEL", "test-model")

        client = LLMClient()
        assert client.api_key == "test-key"
        assert client.base_url == "https://test.example.com/v1"
        assert client.model == "test-model"

    def test_init_with_kwargs(self):
        """通过参数传入配置"""
        client = LLMClient(
            api_key="test-key",
            base_url="https://test.example.com/v1",
            model="test-model",
            timeout=30,
            max_retries=5,
        )
        assert client.api_key == "test-key"
        assert client.base_url == "https://test.example.com/v1"
        assert client.model == "test-model"
        assert client.timeout == 30
        assert client.max_retries == 5


class TestLLMClientMatchAudience:
    """测试 LLMClient.match_audience()"""

    @patch("llm_client.OpenAI")
    def test_match_audience_parse_success(self, mock_openai, monkeypatch):
        """成功解析返回格式"""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="85|受众高度匹配"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        client = LLMClient()
        result = client.match_audience("大学生、应届生", "大学生和应届生")

        assert "score" in result
        assert "reason" in result
        assert result["score"] == 85.0
        assert result["reason"] == "受众高度匹配"

    @patch("llm_client.OpenAI")
    def test_match_audience_score_clipped(self, mock_openai, monkeypatch):
        """分数限制在 0-100"""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="150|超出范围"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        client = LLMClient()
        result = client.match_audience("大学生", "大学生")

        assert result["score"] == 100.0

    @patch("llm_client.OpenAI")
    def test_match_audience_parse_failure_fallback(self, mock_openai, monkeypatch):
        """解析失败时回退到默认值"""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="invalid format"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        client = LLMClient()
        result = client.match_audience("大学生", "大学生")

        assert result["score"] == 50.0
        assert "评估中" in result["reason"]


class TestLLMClientParseDemandText:
    """测试 LLMClient.parse_demand_text()"""

    @patch("llm_client.OpenAI")
    def test_parse_demand_text_success(self, mock_openai, monkeypatch):
        """JSON 解析成功返回结构化数据"""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"budget_min": 1000, "budget_max": 3000, "platforms": ["小红书"], "confidence": 0.9}'))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        client = LLMClient()
        result = client.parse_demand_text("我们要找小红书达人，预算1000-3000")

        assert "budget_min" in result
        assert "budget_max" in result
        assert "platforms" in result
        assert "confidence" in result
        assert result["confidence"] == 0.9

    @patch("llm_client.OpenAI")
    def test_parse_demand_text_adds_confidence(self, mock_openai, monkeypatch):
        """缺少 confidence 字段时自动添加"""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"budget_min": 1000}'))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        client = LLMClient()
        result = client.parse_demand_text("测试文本")

        assert "confidence" in result
        assert result["confidence"] == 0.5

    @patch("llm_client.OpenAI")
    def test_parse_demand_text_json_decode_failure(self, mock_openai, monkeypatch):
        """JSON 解析失败时返回空结构"""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="not valid json"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        client = LLMClient()
        result = client.parse_demand_text("测试文本")

        assert result["confidence"] == 0.0
        assert result["platforms"] == []
        assert result["budget_min"] is None

    @patch("llm_client.OpenAI")
    def test_parse_demand_text_strips_markdown(self, mock_openai, monkeypatch):
        """去除 markdown 代码块标记"""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='```json\n{"budget_min": 1000}\n```'))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        client = LLMClient()
        result = client.parse_demand_text("测试文本")

        assert result["budget_min"] == 1000


class TestLLMClientGenerateReason:
    """测试 LLMClient.generate_reason()"""

    @patch("llm_client.OpenAI")
    def test_generate_reason_returns_string(self, mock_openai, monkeypatch):
        """生成推荐理由返回字符串"""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="推荐理由文本"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        client = LLMClient()
        reason = client.generate_reason(
            kol_name="测试达人",
            platform="小红书",
            followers=50000,
            price=1200,
            engagement_rate=3.8,
            conversion_rate=3.5,
            cooperation_count=15,
            audience_match_reason="受众匹配",
        )

        assert isinstance(reason, str)
        assert reason == "推荐理由文本"


class TestLLMClientGenerateAdvice:
    """测试 LLMClient.generate_advice()"""

    @patch("llm_client.OpenAI")
    def test_generate_advice_returns_string(self, mock_openai, monkeypatch):
        """生成投放建议返回字符串"""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="投放建议文本"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        client = LLMClient()
        advice = client.generate_advice(
            top_kols=[{"kol_name": "达人A", "platform": "小红书", "followers": 50000, "price": 1200, "total_score": 85}],
            total_budget=15000,
            platform_distribution={"小红书": 1},
        )

        assert isinstance(advice, str)
        assert advice == "投放建议文本"
