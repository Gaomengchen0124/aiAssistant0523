# AI KOL / 达人匹配助手

基于 AI 的 KOL（达人）智能推荐系统。输入品牌投放需求，系统自动从达人库中筛选并推荐 TOP 10 最合适的达人，附带匹配分数、推荐理由、预估 ROI 和投放建议。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10+、Pandas、Flask |
| LLM | DeepSeek API（OpenAI SDK 兼容） |
| 前端 | HTML5、CSS3、原生 JavaScript、ECharts |
| 数据 | CSV（90 条模拟达人数据） |
| 测试 | pytest、pytest-cov |

---

## 快速开始

### 1. 克隆/下载项目

```bash
cd aiAssistant0523
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制配置模板，填入你的 DeepSeek API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```
LLM_API_KEY=sk-your-api-key-here
```

> API Key 申请地址：https://platform.deepseek.com/

### 4. 启动服务

```bash
python web/app.py
```

服务启动后，浏览器访问：

```
http://127.0.0.1:5000
```

---

## 项目结构

```
aiAssistant0523/
├── data/
│   └── influencers.csv          # 达人数据库（90 条模拟数据）
├── src/                         # 后端核心模块
│   ├── csv_loader.py            # CSV 加载与清洗
│   ├── filters.py               # 需求解析 + 初步筛选
│   ├── scoring.py               # 受众匹配 / 性价比 / 风险 / 综合评分
│   ├── roi_calculator.py        # ROI 预估计算
│   ├── ranking.py               # TOP 10 排序
│   ├── formatters.py            # 输出格式化（Markdown）
│   ├── budget_allocator.py      # 预算分配算法
│   ├── llm_client.py            # DeepSeek API 封装
│   └── pipeline.py              # 11 步原子工作流编排器
├── web/                         # 前端 + Flask API
│   ├── app.py                   # Flask 后端（API 路由）
│   ├── index.html               # 首页推荐（表单 + 结果）
│   ├── explore.html             # 达人库（筛选 + 图表）
│   ├── detail.html              # 达人详情
│   ├── history.html             # 历史记录
│   ├── settings.html            # 系统设置（LLM 配置 + 数据上传）
│   ├── css/style.css            # 样式
│   └── js/                      # 前端逻辑
├── tests/                       # 自动化测试
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   └── fixtures/                # 测试数据
├── main.py                      # CLI 命令行入口
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量模板
└── README.md                    # 本文件
```

---

## 核心功能

1. **智能推荐**：输入目标受众、内容领域、预算、平台，AI 自动推荐 TOP 10 达人
2. **多维度评分**：受众匹配度（40%）+ 性价比（35%）+ 风险评估（25%）
3. **预算分配**：按匹配分权重自动分配预算，预留 20% 测试资金
4. **可视化**：ECharts 饼图（预算分配）+ 柱状图（平台分布）
5. **历史记录**：保存每次推荐结果，支持查看和删除
6. **达人库**：独立浏览全部达人，支持筛选/排序/搜索
7. **立即联系**：自动生成合作话术（需手动粘贴发送）

---

## API 文档

### 推荐相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/recommend` | 提交需求，返回 TOP 10 推荐 |
| POST | `/api/parse_demand` | 自由文本需求解析 |
| POST | `/api/allocate_budget` | 预算分配计算 |

### 达人相关

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/kol/<kol_id>` | 获取单个达人详情 |
| GET | `/api/platforms` | 获取平台列表 |
| GET | `/api/fields` | 获取内容领域列表 |
| POST | `/api/reload_data` | 重新加载 CSV 数据 |

### 历史记录

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/history` | 获取历史记录列表 |
| GET | `/api/history/<id>` | 获取单条历史详情 |
| DELETE | `/api/history/<id>` | 删除历史记录 |

### 设置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/settings` | 读取配置（API Key 脱敏） |
| POST | `/api/settings` | 保存配置 |
| POST | `/api/test_connection` | 测试 DeepSeek API 连通性 |

---

## 测试

```bash
# 运行全部测试
pytest

# 查看覆盖率报告
pytest --cov=src --cov=web
```

- 总计 **176** 个测试用例
- 整体代码覆盖率 **80%**

---

## 数据说明

`data/influencers.csv` 包含 90 条模拟达人数据，覆盖：
- **4 个平台**：小红书、抖音、B站、微博
- **8 个领域**：校园、职场、美妆、科技、美食、旅游、健身、母婴
- **字段**：昵称、平台、粉丝数、内容领域、报价、互动率、转化率、受众画像、合作次数、风险备注

> 报价/转化率/受众画像/合作次数/风险备注为模拟生成数据，已显性标注。

---

## 部署

### 本地开发

```bash
python web/app.py
```

### 生产环境（腾讯云）

1. 安装依赖：`pip install -r requirements.txt`
2. 配置 `.env`
3. 使用 Gunicorn 启动：
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 "web.app:app"
   ```
4. Nginx 反向代理到 5000 端口

---

## 许可证

MIT
