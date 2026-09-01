# DataPilot · AI 数据分析助手

> 把一份表格变成可决策的结论——上传、自动分析、对话追问、一键导出报告。

**🔗 在线体验**：https://data-pilot-nn2bt.streamlit.app/

DataPilot 是面向**业务/运营/产品同学**的 AI 数据分析产品：不需要写代码，也不需要懂 Python，
上传 CSV / Excel 就能完成过去要数据分析师花半天做的事。本项目由原本的 AI 数据分析 demo 重构为
产品级应用，强调**价值主张清晰、交互稳定、永远可用**。

## 产品定位

- **目标用户**：需要处理业务数据但非专业数据分析师的人（运营、产品、销售、创业者、学生）。
- **核心痛点**：数据散在表格里，看不懂、不会分析、出报告慢。
- **价值主张**：上传即分析，用自然语言追问，结论可下载沉淀。
- **差异化**：大模型 / 本地规则双模——没配 API Key 也能用，配置后分析能力升级。

## 核心功能

| 模块 | 能力 |
| --- | --- |
| 数据概览 | 自动画像：规模、字段类型、缺失值、关键统计量、相关性热力图 |
| 智能图表 | 按字段类型推荐图表（柱状/折线/散点/直方图/箱线/饼图/热力），支持自定义选轴 |
| AI 助手 | 对话式分析：缺失、相关性、Top 排行、分布、趋势；大模型或本地规则兜底 |
| 分析报告 | 把画像 + 图表 + 问答沉淀为 Markdown 报告，一键下载 |

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
# 浏览器打开 http://localhost:8501
```

## 配置 AI（可选，三种方式）

不配置也能完整使用（走本地规则兜底）。配置后 AI 助手升级为大模型。
**优先级：页面填写 > 环境变量 > Streamlit secrets。**

### 方式一：页面内填写（最方便，改完立即生效）

在应用左侧栏展开 **⚙️ AI 接口设置**，填入 API Key / Base URL / 模型名，点 **🔌 测试连接** 验证。
密钥仅保存在当前会话内存中，**不写入代码、不上传、不落盘**。

### 方式二：环境变量

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://api.openai.com/v1"   # 兼容其它供应商可改
export OPENAI_MODEL="gpt-4o-mini"
```

### 方式三：Streamlit secrets（部署到线上时推荐）

在 `.streamlit/secrets.toml` 或 Streamlit Cloud 的 App 设置里填：

```toml
OPENAI_API_KEY = "sk-..."
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-4o-mini"
```

> 兼容任何 **OpenAI 格式**的接口（DeepSeek / 通义千问 / 智谱 / 中转地址均可），改 `OPENAI_BASE_URL` 即可，国内无需翻墙。
>
> 安全说明：AI 助手**只读取数据并返回分析文本/图表建议，绝不执行大模型生成的代码**，避免注入风险。
> 仓库已用 `.gitignore` 忽略 `.streamlit/secrets.toml`，密钥不会误提交。

## 部署（Streamlit Cloud，免费）

1. 代码推送到 GitHub 公开仓库（本项目：`data-pilot`）。
2. 打开 [share.streamlit.io](https://share.streamlit.io) → 用 GitHub 登录 → **New app**。
3. 选仓库 `data-pilot`、分支 `main`、入口文件 `app.py` → Deploy。
4. （可选）在 App 设置 → Secrets 填入上面的 API 配置，线上也能用大模型。
5. 部署完成后得到 `https://<你的名字>-data-pilot.streamlit.app` 公网链接，可直接放进简历/作品集。

> 部署后代码更新会自动同步：本地改完推到 GitHub，线上 App 会自动重新部署。

> ⚠️ **务必检查可见性**：Streamlit Cloud 新应用默认是 **Private**（访客点开会被要求登录）。
> 进 https://share.streamlit.io → 选应用 → 右下角 **Settings（⚙️）→ Sharing**，把可见性改为 **Public**，
> 否则别人点链接看不到内容。

## 目录结构

```
app.py            # 入口：首页 + 工作区（概览/图表/AI/报告）
eda.py            # 数据接入与自动画像
charts.py         # 智能图表推荐与 plotly 渲染
ai_assistant.py   # 对话式 AI 助手（LLM + 本地兜底）
report.py         # Markdown 报告生成
requirements.txt  # 依赖
.streamlit/       # 主题与 server 配置
```

## 后续路线（MVP → 增长）

- [ ] 多文件关联分析（按关键字段 join）
- [ ] 报告导出 PDF / PPT
- [ ] 用户保存分析会话（账号体系）
- [ ] 接入更多数据源（数据库 / API）
- [ ] 模板化分析（周报、销转诊断一键生成）
