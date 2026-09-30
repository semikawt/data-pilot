# DataPilot · AI 数据分析助手

> 把一份表格变成可决策的结论——上传、自动分析、对话追问、一键导出报告。

**🔗 在线体验**：https://data-pilot-nn2bt.streamlit.app/
**📦 代码仓库**：https://github.com/semikawt/data-pilot

---

## 它解决什么问题

业务、运营、产品同学每天面对 Excel，但「想看数据」这件事的真实成本很高：不会写 SQL、不懂透视表，
想看一个趋势得排队找数据分析师取数。

DataPilot 把这条链路压缩成一步——**上传表格，直接用自然语言问**。不需要写代码，也不需要懂 Python，
过去要数据分析师花半天做的事，现在自己几分钟完成。

## 产品定位

| 维度 | 内容 |
| --- | --- |
| 目标用户 | 需要处理业务数据但非专业数据分析师的人（运营、产品、销售、创业者、学生） |
| 核心痛点 | 数据散在表格里，看不懂、不会分析、出报告慢 |
| 价值主张 | 上传即分析，用自然语言追问，结论可下载沉淀 |
| 差异化 | 大模型 / 本地规则**双模**——没配 API Key 也能用，配置后分析能力升级，**永远可用** |

## 核心功能

| 模块 | 能力 |
| --- | --- |
| 数据概览 | 自动画像：规模、字段类型、缺失值、关键统计量、相关性热力图 |
| 智能图表 | 按字段类型推荐图表（柱状 / 折线 / 散点 / 直方图 / 箱线 / 饼图 / 热力），支持自定义选轴 |
| AI 助手 | 对话式分析：缺失、相关性、Top 排行、分布、趋势；大模型或本地规则兜底 |
| 分析报告 | 把画像 + 图表 + 问答沉淀为 Markdown 报告，一键下载 |

## 技术实现

- **框架**：Streamlit 单页应用（首页价值主张 + 工作区四个 Tab），Plotly 负责交互式图表。
- **数据层**：pandas 统一承接 CSV / Excel，多文件同时载入与切换比对。
- **缓存**：`@st.cache_data` 缓存数据画像与图表计算结果，解决大数据集下「越聊越慢」的性能问题。
- **AI 层**：兼容任意 OpenAI 格式接口（OpenAI / DeepSeek / 通义千问 / 智谱 / 中转地址），
  改 `OPENAI_BASE_URL` 即可切换供应商，国内无需额外网络条件。
- **可用性设计**：
  - **降级机制**——未配置 API Key 时自动走本地规则分析，功能不缺失、响应即时。
  - **密钥安全**——支持页面内临时填写（仅存会话内存，不落盘、不上传），或走环境变量 / Streamlit Secrets；
    `.streamlit/secrets.toml` 已被 `.gitignore` 忽略。
  - **不执行模型生成的代码**——AI 只读取数据并返回分析文本与图表建议，规避代码注入风险。
  - **版本兼容**——针对 Streamlit `use_container_width` → `width` 的参数变更做了运行时探测自动降级。

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
# 浏览器打开 http://localhost:8501
```

## 配置 AI（可选）

不配置也能完整使用。**优先级：页面填写 > 环境变量 > Streamlit secrets。**

1. **页面内填写（最方便）**：应用左侧栏展开 **⚙️ AI 接口设置**，填入 API Key / Base URL / 模型名，
   点 **🔌 测试连接** 验证。密钥仅保存在当前会话内存中。
2. **环境变量**：

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4o-mini"
```

3. **Streamlit Secrets**（部署环境推荐）：在 App 设置 → Secrets 中填同样的三个键值。

## 部署

托管于 Streamlit Community Cloud，关联本仓库 `main` 分支的 `app.py`。代码推送后自动重新部署。

## 目录结构

```
app.py            # 入口：首页 + 工作区（概览 / 图表 / AI / 报告）
eda.py            # 数据接入与自动画像
charts.py         # 智能图表推荐与 Plotly 渲染
ai_assistant.py   # 对话式 AI 助手（大模型 + 本地规则兜底）
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
