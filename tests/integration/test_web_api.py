"""
Flask Web API 集成测试
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "web"))

from web.app import app

PROJECT_ROOT = Path(__file__).parent.parent.parent
WEB_DIR = PROJECT_ROOT / "web"


@pytest.fixture
def client(monkeypatch):
    """Flask test client"""
    app.config["TESTING"] = True

    # 切换到 web 目录使相对路径 ../data/influencers.csv 正确
    monkeypatch.chdir(WEB_DIR)

    with app.test_client() as client:
        yield client


class TestAPIRecommend:
    """测试 POST /api/recommend"""

    def test_recommend_success(self, client):
        """正常推荐请求"""
        response = client.post(
            "/api/recommend",
            data=json.dumps({
                "target_audience": "大学生和应届生",
                "content_field": "校园",
                "budget_range": "1000-3000",
                "platforms": "小红书,抖音",
                "engagement_rate_min": "3.0",
            }),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "top10" in data
        assert "report" in data
        assert len(data["top10"]) > 0

    def test_recommend_no_json(self, client):
        """请求体不是 JSON 时"""
        response = client.post("/api/recommend", data="not json")
        assert response.status_code == 500

    def test_recommend_response_structure(self, client):
        """推荐响应结构完整"""
        response = client.post(
            "/api/recommend",
            data=json.dumps({
                "target_audience": "大学生",
                "content_field": "校园",
                "budget_range": "1000-3000",
                "platforms": "小红书",
            }),
            content_type="application/json",
        )

        data = response.get_json()
        assert "success" in data
        assert "report" in data
        assert "top10" in data
        assert "budget_allocation" in data
        assert "platform_summary" in data
        assert "history_id" in data


class TestAPIKOLs:
    """测试 GET /api/kols"""

    def test_get_kols_success(self, client):
        """获取全部达人列表"""
        response = client.get("/api/kols")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) > 0
        assert "total" in data

    def test_get_kols_fields(self, client):
        """达人列表包含所有字段"""
        response = client.get("/api/kols")
        data = response.get_json()

        kol = data["data"][0]
        required_fields = [
            "kol_id", "kol_name", "platform", "followers", "field",
            "price", "avg_likes", "avg_comments", "engagement_rate",
            "conversion_rate", "audience", "cooperation_count", "risk_note",
        ]
        for field in required_fields:
            assert field in kol, f"缺少字段: {field}"


class TestAPIKOLDetail:
    """测试 GET /api/kol/<id>"""

    def test_get_kol_success(self, client):
        """获取单个达人详情"""
        response = client.get("/api/kol/KOL_001")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["kol_id"] == "KOL_001"

    def test_get_kol_not_found(self, client):
        """达人不存在时返回 404"""
        response = client.get("/api/kol/NONEXISTENT")
        assert response.status_code == 404

        data = response.get_json()
        assert data["success"] is False


class TestAPIHistory:
    """测试 GET /api/history"""

    def test_get_history(self, client):
        """获取历史记录列表"""
        response = client.get("/api/history")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert "data" in data


class TestAPIPlatforms:
    """测试 GET /api/platforms"""

    def test_get_platforms(self, client):
        """获取平台列表"""
        response = client.get("/api/platforms")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert "data" in data
        platforms = data["data"]
        assert "小红书" in platforms
        assert "抖音" in platforms
        assert "B站" in platforms
        assert "微博" in platforms


class TestAPIFields:
    """测试 GET /api/fields"""

    def test_get_fields(self, client):
        """获取内容领域列表"""
        response = client.get("/api/fields")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) > 0


class TestAPIAllocateBudget:
    """测试 POST /api/allocate_budget"""

    def test_allocate_budget_success(self, client):
        """预算分配成功"""
        response = client.post(
            "/api/allocate_budget",
            data=json.dumps({
                "top10": [
                    {
                        "kol_id": "K1", "kol_name": "达人A", "platform": "小红书",
                        "followers": 50000, "price": 1200, "total_score": 85,
                        "conversion_rate": 3.5,
                    },
                    {
                        "kol_id": "K2", "kol_name": "达人B", "platform": "抖音",
                        "followers": 80000, "price": 2000, "total_score": 80,
                        "conversion_rate": 3.2,
                    },
                ],
                "total_budget": 10000,
                "num_kols": 2,
            }),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "budget_allocation" in data
        assert "platform_summary" in data

    def test_allocate_budget_empty_top10(self, client):
        """空 top10 时返回错误"""
        response = client.post(
            "/api/allocate_budget",
            data=json.dumps({"top10": [], "total_budget": 10000}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_allocate_budget_roi_mode(self, client):
        """ROI 模式预算分配"""
        response = client.post(
            "/api/allocate_budget",
            data=json.dumps({
                "top10": [
                    {
                        "kol_id": "K1", "kol_name": "达人A", "platform": "小红书",
                        "followers": 50000, "price": 1200, "total_score": 85,
                        "conversion_rate": 3.5,
                    },
                ],
                "total_budget": 10000,
                "target_roi": 2.0,
            }),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True


class TestAPIStaticFiles:
    """测试静态文件服务"""

    def test_index_page(self, client):
        """首页可访问"""
        response = client.get("/")
        assert response.status_code == 200

    def test_static_html(self, client):
        """HTML 页面可访问"""
        for page in ["index.html", "explore.html", "history.html", "settings.html", "detail.html"]:
            response = client.get(f"/{page}")
            assert response.status_code == 200
