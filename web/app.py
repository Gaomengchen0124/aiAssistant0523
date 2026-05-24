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
from scoring import CompositeScorer, RiskAssessor, ValueScorer

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
    获取单个达人详情（含综合评分）
    """
    try:
        loader = CSVLoader("../data/influencers.csv")
        df = loader.load()
        kol = df[df["kol_id"] == kol_id]

        if kol.empty:
            return jsonify({"success": False, "error": "KOL not found"}), 404

        # 计算全库评分，提取当前博主
        scored_df = ValueScorer.score(df)
        risked_df = RiskAssessor.assess_batch(scored_df)
        final_df = CompositeScorer.compute(risked_df)

        current = final_df[final_df["kol_id"] == kol_id].iloc[0]
        record = current.to_dict()

        numeric_fields = ["followers", "price", "avg_likes", "avg_comments", "engagement_rate", "conversion_rate", "cooperation_count"]
        for f in numeric_fields:
            if f in record:
                record[f] = float(record[f]) if f in ["engagement_rate", "conversion_rate"] else int(record[f])

        # 添加评分字段
        record["total_score"] = round(float(current["total_score"]), 1)
        record["match_score"] = round(float(current["match_score"]), 1)
        record["value_score"] = round(float(current["value_score"]), 1)
        record["risk_score"] = round(float(current["risk_score"]), 1)
        record["risk_level"] = str(current["risk_level"])

        return jsonify({"success": True, "data": record})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/kol/<kol_id>/comparison", methods=["GET"])
def get_kol_comparison(kol_id):
    """
    获取达人同平台对比数据（百分位、优势劣势、类似博主）
    """
    try:
        loader = CSVLoader("../data/influencers.csv")
        df = loader.load()
        kol = df[df["kol_id"] == kol_id]

        if kol.empty:
            return jsonify({"success": False, "error": "KOL not found"}), 404

        # 计算全库评分
        scored_df = ValueScorer.score(df)
        risked_df = RiskAssessor.assess_batch(scored_df)
        final_df = CompositeScorer.compute(risked_df)

        current = final_df[final_df["kol_id"] == kol_id].iloc[0]
        current_platform = current["platform"]
        current_field = current["field"]

        # 同平台博主
        platform_df = final_df[final_df["platform"] == current_platform]
        comparison_scope = "同平台"

        # 如果同平台只有1人，使用全库
        if len(platform_df) <= 1:
            platform_df = final_df.copy()
            comparison_scope = "全库"

        def calc_percentile(series, value):
            """计算 value 在 series 中的百分位（0-100）"""
            return (series < value).mean() * 100

        # 计算百分位
        percentiles = {
            "followers": round(calc_percentile(platform_df["followers"], current["followers"]), 1),
            "engagement_rate": round(calc_percentile(platform_df["engagement_rate"], current["engagement_rate"]), 1),
            "conversion_rate": round(calc_percentile(platform_df["conversion_rate"], current["conversion_rate"]), 1),
            "value_score": round(calc_percentile(platform_df["value_score"], current["value_score"]), 1),
        }

        # 优势和劣势
        metric_labels = {
            "followers": "粉丝数",
            "engagement_rate": "互动率",
            "conversion_rate": "转化率",
            "value_score": "性价比",
        }
        metric_formats = {
            "followers": lambda v: f"{int(v):,}",
            "engagement_rate": lambda v: f"{v:.1f}%",
            "conversion_rate": lambda v: f"{v:.1f}%",
            "value_score": lambda v: f"{v:.1f}分",
        }

        advantages = []
        disadvantages = []

        for key, label in metric_labels.items():
            p = percentiles[key]
            fmt = metric_formats[key]
            if p > 60:
                advantages.append({
                    "metric": label,
                    "value": fmt(current[key]),
                    "raw_value": float(current[key]),
                    "percentile": p,
                })
            elif p < 40:
                disadvantages.append({
                    "metric": label,
                    "value": fmt(current[key]),
                    "raw_value": float(current[key]),
                    "percentile": p,
                })

        # 排序并截取
        advantages = sorted(advantages, key=lambda x: x["percentile"], reverse=True)[:3]
        disadvantages = sorted(disadvantages, key=lambda x: x["percentile"])[:3]

        # 类似博主：策略1=同平台+同领域，策略2=同领域，策略3=同平台
        current_fields = set(str(current_field).split("/"))

        def has_common_field(field_str):
            return len(set(str(field_str).split("/")) & current_fields) > 0

        similar = final_df[
            (final_df["platform"] == current_platform) &
            (final_df["kol_id"] != kol_id) &
            (final_df["field"].apply(has_common_field))
        ]

        if len(similar) < 3:
            similar = final_df[
                (final_df["kol_id"] != kol_id) &
                (final_df["field"].apply(has_common_field))
            ]

        if len(similar) < 3:
            similar = final_df[
                (final_df["platform"] == current_platform) &
                (final_df["kol_id"] != kol_id)
            ]

        # 计算欧几里得距离并排序
        def calc_distance(row):
            metrics = ["followers", "engagement_rate", "conversion_rate"]
            dist = 0
            for m in metrics:
                p_min = final_df[m].min()
                p_max = final_df[m].max()
                if p_max > p_min:
                    curr_norm = (current[m] - p_min) / (p_max - p_min)
                    row_norm = (row[m] - p_min) / (p_max - p_min)
                    dist += (curr_norm - row_norm) ** 2
            return dist ** 0.5

        similar = similar.copy()
        similar["distance"] = similar.apply(calc_distance, axis=1)
        similar = similar.sort_values("distance").head(4)

        similar_kols = []
        for _, row in similar.iterrows():
            similar_kols.append({
                "kol_id": row["kol_id"],
                "kol_name": row["kol_name"],
                "platform": row["platform"],
                "followers": int(row["followers"]),
                "engagement_rate": float(row["engagement_rate"]),
                "conversion_rate": float(row["conversion_rate"]),
                "price": int(row["price"]),
            })

        # ========== 雷达图数据：5维能力画像 ==========
        def normalize(series, value):
            """将 value 按 series 的 min-max 归一化到 0-100"""
            s_min = series.min()
            s_max = series.max()
            if s_max > s_min:
                return round((value - s_min) / (s_max - s_min) * 100, 1)
            return 50.0

        radar_metrics = {
            "粉丝影响力": ("followers", platform_df),
            "互动能力": ("engagement_rate", platform_df),
            "转化能力": ("conversion_rate", platform_df),
            "性价比": ("value_score", platform_df),
            "合作经验": ("cooperation_count", platform_df),
        }

        radar_current = []
        radar_average = []
        for label, (col, df_ref) in radar_metrics.items():
            radar_current.append(normalize(df_ref[col], current[col]))
            radar_average.append(normalize(df_ref[col], df_ref[col].mean()))

        radar_data = {
            "indicators": [{"name": k, "max": 100} for k in radar_metrics.keys()],
            "current": radar_current,
            "average": radar_average,
        }

        # ========== 散点图数据：同平台分布 ==========
        scatter_data = []
        for _, row in platform_df.iterrows():
            scatter_data.append({
                "kol_id": row["kol_id"],
                "kol_name": row["kol_name"],
                "engagement_rate": round(float(row["engagement_rate"]), 2),
                "conversion_rate": round(float(row["conversion_rate"]), 2),
                "followers": int(row["followers"]),
                "is_current": row["kol_id"] == kol_id,
            })

        # ========== 横向对比条形图数据 ==========
        bar_metrics = {
            "粉丝数": ("followers", lambda v: f"{int(v):,}"),
            "互动率": ("engagement_rate", lambda v: f"{v:.2f}%"),
            "转化率": ("conversion_rate", lambda v: f"{v:.2f}%"),
            "性价比": ("value_score", lambda v: f"{v:.1f}"),
        }

        bar_comparison = []
        for label, (col, fmt) in bar_metrics.items():
            bar_comparison.append({
                "metric": label,
                "current": round(float(current[col]), 2),
                "current_fmt": fmt(current[col]),
                "current_norm": normalize(platform_df[col], current[col]),
                "average": round(float(platform_df[col].mean()), 2),
                "average_fmt": fmt(platform_df[col].mean()),
                "average_norm": normalize(platform_df[col], platform_df[col].mean()),
            })

        return jsonify({
            "success": True,
            "data": {
                "kol_id": kol_id,
                "platform": current_platform,
                "comparison_scope": comparison_scope,
                "percentiles": percentiles,
                "advantages": advantages,
                "disadvantages": disadvantages,
                "similar_kols": similar_kols,
                "radar": radar_data,
                "scatter": scatter_data,
                "bar_comparison": bar_comparison,
            }
        })

    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "detail": traceback.format_exc()}), 500


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


# ========== Settings Management ==========

ENV_FILE = Path(__file__).parent.parent / ".env"
DATA_CSV = Path(__file__).parent.parent / "data" / "influencers.csv"


def _read_env():
    """读取 .env 文件为 dict，保留原始格式"""
    config = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    config[key.strip()] = val.strip()
    return config


def _write_env(config):
    """将 dict 写回 .env 文件"""
    lines = []
    for key, val in sorted(config.items()):
        lines.append(f"{key}={val}")
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _mask_key(key):
    """脱敏 API Key，如 sk-70****46a3"""
    if not key or len(key) < 8:
        return key
    return key[:4] + "****" + key[-4:]


@app.route("/api/settings", methods=["GET"])
def get_settings():
    """获取当前配置（API Key 脱敏）"""
    try:
        cfg = _read_env()

        # 尝试获取数据量
        data_count = 0
        try:
            loader = CSVLoader("../data/influencers.csv")
            df = loader.load()
            data_count = len(df)
        except Exception:
            pass

        return jsonify({
            "success": True,
            "data": {
                "api_key": _mask_key(cfg.get("LLM_API_KEY", "")),
                "base_url": cfg.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
                "model": cfg.get("LLM_MODEL", "deepseek-chat"),
                "timeout": int(cfg.get("LLM_TIMEOUT", "60")),
                "data_path": "data/influencers.csv",
                "data_count": data_count,
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/settings", methods=["POST"])
def save_settings():
    """保存配置到 .env 文件"""
    try:
        data = request.get_json() or {}
        api_key = data.get("api_key", "").strip()
        base_url = data.get("base_url", "").strip()
        model = data.get("model", "").strip()
        timeout = data.get("timeout")

        # 校验
        if api_key and not api_key.startswith("sk-"):
            return jsonify({"success": False, "error": "API Key 必须以 sk- 开头"}), 400
        if timeout is not None:
            try:
                timeout = int(timeout)
                if not (10 <= timeout <= 300):
                    raise ValueError
            except ValueError:
                return jsonify({"success": False, "error": "超时时间必须在 10-300 秒之间"}), 400

        cfg = _read_env()

        if api_key:
            cfg["LLM_API_KEY"] = api_key
        if base_url:
            cfg["LLM_BASE_URL"] = base_url
        if model:
            cfg["LLM_MODEL"] = model
        if timeout is not None:
            cfg["LLM_TIMEOUT"] = str(timeout)

        # 确保默认值存在
        if "LLM_MAX_RETRIES" not in cfg:
            cfg["LLM_MAX_RETRIES"] = "3"

        _write_env(cfg)
        return jsonify({"success": True, "message": "设置已保存"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/test_connection", methods=["POST"])
def test_connection():
    """测试 LLM API 连通性"""
    try:
        data = request.get_json() or {}
        api_key = data.get("api_key", "").strip()
        base_url = data.get("base_url", "").strip()
        model = data.get("model", "").strip()
        timeout = data.get("timeout")

        # 如果收到的是脱敏值（如 sk-7****46a3），从 .env 读取真实 Key
        if "****" in api_key:
            cfg = _read_env()
            api_key = cfg.get("LLM_API_KEY", "")

        if not api_key:
            return jsonify({"success": False, "error": "API Key 不能为空"}), 400

        try:
            timeout = int(timeout) if timeout else 60
        except ValueError:
            timeout = 60

        import time
        start = time.time()

        try:
            client = LLMClient(
                api_key=api_key,
                base_url=base_url or "https://api.deepseek.com/v1",
                model=model or "deepseek-chat",
                timeout=timeout,
                max_retries=1,
            )
            # 发送极简请求验证连通性
            _ = client._chat("You are a helpful assistant.", "Say 'pong' only.", temperature=0)
            latency = round((time.time() - start) * 1000)
            return jsonify({
                "success": True,
                "message": f"连接成功，延迟 {latency}ms",
                "latency_ms": latency,
            })
        except Exception as e:
            latency = round((time.time() - start) * 1000)
            err_str = str(e)
            if "401" in err_str or "Unauthorized" in err_str:
                message = "认证失败：API Key 无效"
            elif "Connection" in err_str or "connect" in err_str.lower():
                message = "网络错误：无法连接到 API 服务器"
            elif "timeout" in err_str.lower():
                message = "请求超时：请检查网络或增加超时时间"
            else:
                message = f"连接失败：{err_str[:120]}"
            return jsonify({
                "success": False,
                "message": message,
                "latency_ms": latency,
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reload_data", methods=["POST"])
def reload_data():
    """重新加载并验证 CSV 数据"""
    try:
        loader = CSVLoader("../data/influencers.csv")
        df = loader.load()
        ok, errs = loader.validate(df)

        if not ok:
            return jsonify({
                "success": False,
                "error": "数据验证失败",
                "detail": errs,
            }), 500

        return jsonify({
            "success": True,
            "message": f"已加载 {len(df)} 位达人",
            "count": len(df),
            "errors": [],
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("KOL Matcher API Server")
    print("=" * 50)
    print("Open http://127.0.0.1:5000 in your browser")
    print("=" * 50)
    app.run(host="127.0.0.1", port=5000, debug=True)
