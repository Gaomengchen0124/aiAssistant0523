"""
Flask Backend API for KOL Matcher
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# 将 src 加入路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from budget_allocator import BudgetAllocator
from csv_loader import CSVLoader
from llm_client import LLMClient
from pipeline import KOLPipeline

app = Flask(__name__, static_folder=".")
CORS(app)

# 历史记录存储（内存 + 文件）
HISTORY = []
HISTORY_FILE = Path(__file__).parent.parent / "data" / "history.json"


def _load_history():
    """加载历史记录"""
    global HISTORY
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            HISTORY = json.load(f)


def _save_history():
    """保存历史记录"""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(HISTORY, f, ensure_ascii=False, indent=2)


_load_history()


@app.route("/")
def index():
    """返回首页"""
    return send_from_directory(".", "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    """服务静态文件（HTML/CSS/JS）"""
    return send_from_directory(".", filename)


@app.route("/api/recommend", methods=["POST"])
def recommend():
    """
    推荐接口
    每次请求创建新的 Pipeline 实例，避免状态冲突
    """
    try:
        data = request.get_json() or {}

        # 每次请求创建新实例，避免并发状态冲突
        pipeline = KOLPipeline(csv_path="../data/influencers.csv", use_llm=True)

        # 运行 Pipeline
        report = pipeline.run(data)

        # 预算分配
        total_budget = data.get("total_budget", 15000)
        budget_result = BudgetAllocator.allocate(pipeline.top10, total_budget=total_budget)
        budget_advice = BudgetAllocator.format_advice(budget_result)

        # 合并投放建议（Pipeline 生成的 + BudgetAllocator 生成的）
        full_report = report + "\n\n" + budget_advice

        # 序列化 top10 为 dict，带正确排名
        top10_records = pipeline.top10.to_dict("records") if pipeline.top10 is not None else []
        simplified_top10 = []
        for rank, row in enumerate(top10_records, start=1):
            simplified_top10.append({
                "rank": rank,
                "kol_id": row.get("kol_id"),
                "kol_name": row.get("kol_name"),
                "platform": row.get("platform"),
                "followers": int(row.get("followers", 0)),
                "price": int(row.get("price", 0)),
                "engagement_rate": float(row.get("engagement_rate", 0)),
                "conversion_rate": float(row.get("conversion_rate", 0)),
                "total_score": round(float(row.get("total_score", 0)), 1),
                "match_score": round(float(row.get("match_score", 0)), 1),
                "roi": row.get("roi", ""),
                "risk_level": row.get("risk_level", "低"),
                "cooperation_count": int(row.get("cooperation_count", 0)),
                "recommend_reason": row.get("recommend_reason", ""),
                "audience": row.get("audience", ""),
            })

        # 保存到历史（包含完整 top10）
        history_entry = {
            "id": len(HISTORY) + 1,
            "timestamp": datetime.now().isoformat(),
            "demand": data,
            "top10": simplified_top10,
            "top10_count": len(simplified_top10),
            "avg_score": round(sum(r["total_score"] for r in simplified_top10) / max(len(simplified_top10), 1), 1) if simplified_top10 else 0,
            "budget_allocation": budget_result,
        }
        HISTORY.append(history_entry)
        _save_history()

        return jsonify({
            "success": True,
            "report": full_report,
            "top10": simplified_top10,
            "budget_allocation": budget_result,
            "platform_summary": budget_result.get("platform_summary", {}),
            "history_id": history_entry["id"],
        })

    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "detail": traceback.format_exc()}), 500


@app.route("/api/kols", methods=["GET"])
def get_kols():
    """
    获取全部达人列表（用于达人库页面，不触发 LLM）
    """
    try:
        loader = CSVLoader("../data/influencers.csv")
        df = loader.load()
        ok, errs = loader.validate(df)
        if not ok:
            return jsonify({"success": False, "error": f"数据验证失败: {errs}"}), 500

        records = []
        for _, row in df.iterrows():
            records.append({
                "kol_id": row.get("kol_id"),
                "kol_name": row.get("kol_name"),
                "platform": row.get("platform"),
                "followers": int(row.get("followers", 0)),
                "field": row.get("field"),
                "price": int(row.get("price", 0)),
                "avg_likes": int(row.get("avg_likes", 0)),
                "avg_comments": int(row.get("avg_comments", 0)),
                "engagement_rate": float(row.get("engagement_rate", 0)),
                "conversion_rate": float(row.get("conversion_rate", 0)),
                "audience": row.get("audience"),
                "cooperation_count": int(row.get("cooperation_count", 0)),
                "risk_note": row.get("risk_note"),
            })

        return jsonify({"success": True, "data": records, "total": len(records)})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/kol/<kol_id>", methods=["GET"])
def get_kol(kol_id):
    """
    获取单个达人详情
    """
    try:
        loader = CSVLoader("../data/influencers.csv")
        df = loader.load()
        kol = df[df["kol_id"] == kol_id]

        if kol.empty:
            return jsonify({"success": False, "error": "KOL not found"}), 404

        record = kol.iloc[0].to_dict()
        numeric_fields = ["followers", "price", "avg_likes", "avg_comments", "engagement_rate", "conversion_rate", "cooperation_count"]
        for f in numeric_fields:
            if f in record:
                record[f] = float(record[f]) if f in ["engagement_rate", "conversion_rate"] else int(record[f])

        return jsonify({"success": True, "data": record})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    """获取历史记录列表"""
    return jsonify({"success": True, "data": HISTORY})


@app.route("/api/history/<int:history_id>", methods=["GET"])
def get_history_detail(history_id):
    """获取单条历史记录详情（包含完整 top10）"""
    for h in HISTORY:
        if h["id"] == history_id:
            return jsonify({"success": True, "data": h})
    return jsonify({"success": False, "error": "History not found"}), 404


@app.route("/api/history/<int:history_id>", methods=["DELETE"])
def delete_history(history_id):
    """删除历史记录"""
    global HISTORY
    HISTORY = [h for h in HISTORY if h["id"] != history_id]
    _save_history()
    return jsonify({"success": True})


@app.route("/api/platforms", methods=["GET"])
def get_platforms():
    """获取平台列表"""
    return jsonify({"success": True, "data": ["小红书", "抖音", "B站", "微博"]})


@app.route("/api/fields", methods=["GET"])
def get_fields():
    """获取内容领域列表"""
    try:
        loader = CSVLoader("../data/influencers.csv")
        df = loader.load()
        fields = set()
        for f in df["field"]:
            fields.update(str(f).split("/"))
        return jsonify({"success": True, "data": sorted(fields)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/parse_demand", methods=["POST"])
def parse_demand():
    """
    从自由文本中解析结构化投放需求

    Request: {"text": "我们要推广一款职场技能课程..."}
    Response: {"success": true, "data": {"gender": "不限", "age_min": 22, ...}}
    """
    try:
        data = request.get_json() or {}
        text = data.get("text", "").strip()

        if not text:
            return jsonify({"success": False, "error": "文本不能为空"}), 400

        client = LLMClient()
        result = client.parse_demand_text(text)

        return jsonify({"success": True, "data": result})

    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "detail": traceback.format_exc()}), 500


@app.route("/api/allocate_budget", methods=["POST"])
def allocate_budget():
    """
    预算分配接口（支持人数模式和 ROI 模式）

    Request: {
        "top10": [{...}],
        "total_budget": 15000,
        "num_kols": 5,      // 可选，合作人数模式
        "target_roi": 3.0   // 可选，ROI 模式（1:3）
    }
    """
    try:
        data = request.get_json() or {}
        top10_list = data.get("top10", [])
        total_budget = data.get("total_budget", 15000)
        num_kols = data.get("num_kols")
        target_roi = data.get("target_roi")

        if not top10_list:
            return jsonify({"success": False, "error": "top10 数据不能为空"}), 400

        import pandas as pd
        top10_df = pd.DataFrame(top10_list)

        # 确定使用哪种模式
        if target_roi and target_roi > 0:
            # ROI 模式
            result = BudgetAllocator.allocate_by_roi(top10_df, total_budget, target_roi)
        elif num_kols and num_kols > 0:
            # 人数模式
            result = BudgetAllocator.allocate(top10_df, total_budget=total_budget, top_n=min(num_kols, 10))
        else:
            # 默认模式：TOP5
            result = BudgetAllocator.allocate(top10_df, total_budget=total_budget, top_n=5)

        return jsonify({
            "success": True,
            "budget_allocation": result,
            "platform_summary": result.get("platform_summary", {}),
        })

    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "detail": traceback.format_exc()}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("KOL Matcher API Server")
    print("=" * 50)
    print("Open http://127.0.0.1:5000 in your browser")
    print("=" * 50)
    app.run(host="127.0.0.1", port=5000, debug=True)
