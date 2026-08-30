# -*- coding: utf-8 -*-
"""DataPilot · AI 数据分析助手 —— 产品级入口。
首页（价值主张/流程/功能）+ 工作区（概览/智能图表/AI助手/报告）。
LLM 为可选能力：配置 OPENAI_API_KEY 后 AI 助手走大模型，否则本地规则兜底。"""
import pandas as pd
import streamlit as st

import eda
import charts
import ai_assistant
import report

PRIMARY = "#4472C4"
st.set_page_config(page_title="DataPilot · AI 数据分析助手", page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown(f"""
<style>
.hero {{ background: linear-gradient(135deg,#4472C4,#6f9be8); color:#fff; padding:42px 36px;
        border-radius:14px; margin-bottom:18px; }}
.hero h1 {{ font-size:34px; margin:0 0 8px; letter-spacing:1px; }}
.hero p {{ font-size:16px; opacity:.95; margin:0; }}
.hero .cta {{ margin-top:22px; }}
.btn-primary {{ display:inline-block; background:#fff; color:{PRIMARY}; font-weight:600;
        padding:10px 20px; border-radius:8px; text-decoration:none; margin-right:10px; }}
.btn-ghost {{ display:inline-block; border:1px solid rgba(255,255,255,.7); color:#fff;
        padding:10px 20px; border-radius:8px; text-decoration:none; }}
.step {{ background:#F4F6F9; border-radius:10px; padding:18px; height:100%; }}
.step .n {{ font-size:22px; font-weight:700; color:{PRIMARY}; }}
.feat {{ border:1px solid #E6EAF2; border-radius:10px; padding:16px; height:100%; }}
.feat .t {{ font-weight:600; font-size:15px; margin-bottom:4px; }}
.feat .d {{ color:#5b6472; font-size:13px; }}
.empty {{ text-align:center; color:#8a93a3; padding:40px 0; }}
</style>
""", unsafe_allow_html=True)

# ---------- session state ----------
for k, v in {
    "page": "home", "datasets": {}, "active": None,
    "qa": [], "chart_specs": [], "upload_key": 0,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


def set_data(name, df):
    st.session_state.datasets[name] = df
    st.session_state.active = name
    st.session_state.page = "workspace"
    st.session_state.qa = []
    st.session_state.chart_specs = []


def valid_frames():
    return {k: v for k, v in st.session_state.datasets.items() if isinstance(v, pd.DataFrame)}


# ---------- sidebar ----------
with st.sidebar:
    st.markdown(f"### 📊 DataPilot")
    st.caption("AI 数据分析助手")
    files = st.file_uploader("上传数据（CSV / Excel，可多选）", type=["csv", "xlsx", "xls"],
                             accept_multiple_files=True, key=f"up{st.session_state.upload_key}")
    if files:
        frames = eda.load_dataframes(files)
        ok = False
        for n, df in frames.items():
            if isinstance(df, pd.DataFrame):
                st.session_state.datasets[n] = df
                ok = True
        if ok:
            st.session_state.active = [n for n, v in st.session_state.datasets.items()
                                       if isinstance(v, pd.DataFrame)][-1]
            st.session_state.page = "workspace"
            st.session_state.qa = []
            st.session_state.chart_specs = []
            st.rerun()
        else:
            st.error("文件均解析失败，请检查格式。")

    if st.button("✨ 用样例数据体验", use_container_width=True):
        set_data("样例·销售明细", eda.get_sample_data())

    st.divider()
    vf = valid_frames()
    if vf:
        st.selectbox("当前数据集", list(vf.keys()), index=list(vf.keys()).index(st.session_state.active)
                     if st.session_state.active in vf else 0,
                     key="active_sel",
                     on_change=lambda: st.session_state.__setitem__("active", st.session_state.active_sel))
    if st.button("🏠 返回首页", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

    st.divider()
    llm = ai_assistant.llm_configured()
    st.caption("AI 模式：" + ("大模型（已配置 Key）" if llm else "本地规则（未配置 Key）"))

    # ---- AI 接口设置：支持在页面上直接填自己的 API（优先级最高，即时生效）----
    with st.expander("⚙️ AI 接口设置（可选）"):
        st.caption("填自己的 API 即可升级为大模型分析；留空则用本地规则，功能照常可用。"
                   "密钥仅保存在当前会话，不会写入代码或上传。")
        st.text_input("API Key", type="password",
                      value=st.session_state.get("llm_api_key", ""),
                      key="llm_api_key", placeholder="sk-...（兼容 OpenAI 格式的 Key）")
        st.text_input("Base URL（可留空）", value=st.session_state.get("llm_base_url", ""),
                      key="llm_base_url", placeholder="https://api.openai.com/v1")
        st.text_input("模型名", value=st.session_state.get("llm_model") or "gpt-4o-mini",
                      key="llm_model", placeholder="gpt-4o-mini / deepseek-chat / qwen-plus")
        if st.button("🔌 测试连接", use_container_width=True):
            if not ai_assistant.llm_configured():
                st.error("未检测到可用的 API Key（或缺少 openai 库）。")
            else:
                with st.spinner("正在调用…"):
                    try:
                        c = ai_assistant._client()
                        m = ai_assistant._cfg("OPENAI_MODEL", "gpt-4o-mini")
                        c.chat.completions.create(
                            model=m, messages=[{"role": "user", "content": "回复两个字：正常"}],
                            max_tokens=10)
                        st.success(f"✅ 连接成功（模型：{m}）")
                    except Exception as e:
                        st.error(f"❌ 连接失败：{e}")


def render_home():
    st.markdown(f"""
    <div class="hero">
      <h1>DataPilot · 你的 AI 数据分析助手</h1>
      <p>上传一份表格，剩下的交给 AI：自动画像、智能图表、对话式分析，一键导出报告。</p>
      <div class="cta" style="opacity:.95">👉 在左侧上传 CSV / Excel，或点击「✨ 用样例数据体验」立即试用</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 三步上手")
    cols = st.columns(3)
    steps = [
        ("1", "上传 / 选择数据", "支持 CSV、Excel，多文件切换；内置样例零门槛体验。"),
        ("2", "AI 自动分析", "自动生成数据画像与质量报告，推荐最合适的图表。"),
        ("3", "对话 & 导出", "用自然语言追问数据，沉淀为一份可下载的分析报告。"),
    ]
    for c, (n, t, d) in zip(cols, steps):
        c.markdown(f"<div class='step'><div class='n'>{n}</div><div class='t' style='font-weight:600;margin:6px 0'>{t}</div><div style='color:#5b6472;font-size:13px'>{d}</div></div>", unsafe_allow_html=True)

    st.markdown("#### 核心能力")
    feats = [
        ("📈 自动 EDA", "行列规模、字段类型、缺失值、关键统计量一键呈现。"),
        ("🧭 智能图表", "按数据特征推荐图表，免选轴也能出图。"),
        ("💬 对话分析", "像聊天一样追问：缺失、相关性、Top 排行、趋势。"),
        ("📑 报告导出", "把画像 + 图表 + 问答沉淀为 Markdown 报告。"),
        ("🤖 大模型 / 本地双模", "配 Key 走大模型，没 Key 也能本地分析，永远可用。"),
        ("🗂 多数据集", "同时管理多份表格，随时切换对比。"),
    ]
    fcols = st.columns(3)
    for i, (t, d) in enumerate(feats):
        fcols[i % 3].markdown(f"<div class='feat'><div class='t'>{t}</div><div class='d'>{d}</div></div>", unsafe_allow_html=True)


def render_workspace():
    vf = valid_frames()
    if not vf:
        st.markdown("<div class='empty'>尚未载入数据，请在左侧上传或体验样例。</div>", unsafe_allow_html=True)
        return
    if st.session_state.active not in vf:
        st.session_state.active = list(vf.keys())[0]
    df = vf[st.session_state.active]
    prof = eda.profile_dataframe(df)

    tab1, tab2, tab3, tab4 = st.tabs(["📊 数据概览", "🧭 智能图表", "💬 AI 助手", "📑 分析报告"])

    # ---- 概览 ----
    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("行数", prof["rows"])
        c2.metric("列数", prof["cols"])
        miss_total = sum(prof["missing"].values())
        c3.metric("缺失值", miss_total, delta=None, delta_color="inverse")
        st.markdown("**字段类型**")
        type_df = pd.DataFrame({
            "字段": prof["columns"],
            "类型": [prof["kinds"][c] for c in prof["columns"]],
            "缺失数": [prof["missing"][c] for c in prof["columns"]],
            "缺失率": [f"{prof['missing_pct'][c]}%" for c in prof["columns"]],
        })
        st.dataframe(type_df, use_container_width=True, height=200)
        if prof["describe"]:
            st.markdown("**关键统计（数值列）**")
            st.dataframe(pd.DataFrame(prof["describe"]).T, use_container_width=True)
        if prof["datetime"] and prof["numeric"]:
            pass
        cm = eda.correlation_matrix(df)
        if cm is not None:
            st.markdown("**相关性热力图**")
            st.plotly_chart(charts.render_chart(df, "heatmap", corr=cm), use_container_width=True)
        st.markdown("**数据预览（前 5 行）**")
        st.dataframe(prof["head"], use_container_width=True)

    # ---- 智能图表 ----
    with tab2:
        st.markdown("##### 🤖 推荐图表")
        recs = charts.recommend_charts(df)
        for r in recs:
            with st.expander(r["title"]):
                st.caption(r["reason"])
                if st.button("插入此图", key="rec_" + r["title"]):
                    st.session_state.chart_specs.append(r)
                    st.plotly_chart(charts.render_chart(df, r["type"], r.get("x"), r.get("y")),
                                    use_container_width=True)
        st.divider()
        st.markdown("##### 🛠 自定义图表")
        ctype = st.selectbox("图表类型", charts.VALID_TYPES)
        xcol = st.selectbox("X 轴", prof["columns"], index=0)
        ycol = st.selectbox("Y 轴（部分类型无需）", [None] + prof["columns"], index=0)
        if st.button("生成图表", key="custom_gen"):
            fig = charts.render_chart(df, ctype, xcol, ycol)
            st.session_state.chart_specs.append({"type": ctype, "x": xcol, "y": ycol, "title": f"{ctype}: {xcol}/{ycol}"})
            st.plotly_chart(fig, use_container_width=True)

    # ---- AI 助手 ----
    with tab3:
        st.caption("AI 模式：" + ("大模型" if ai_assistant.llm_configured() else "本地规则兜底（配置 OPENAI_API_KEY 后升级为大模型）"))
        for item in st.session_state.qa:
            with st.chat_message("user"):
                st.write(item["q"])
            with st.chat_message("assistant"):
                st.write(item["a"])
                if item.get("chart"):
                    ch = item["chart"]
                    if ch["type"] == "heatmap":
                        cm2 = eda.correlation_matrix(df)
                        if cm2 is not None:
                            st.plotly_chart(charts.render_chart(df, "heatmap", corr=cm2), use_container_width=True)
                    else:
                        st.plotly_chart(charts.render_chart(df, ch["type"], ch.get("x"), ch.get("y")),
                                        use_container_width=True)
        q = st.chat_input("向这份数据提问，例如：哪类客户复购最高？")
        if q:
            with st.chat_message("user"):
                st.write(q)
            res = ai_assistant.answer_question(df, prof, q, st.session_state.qa)
            with st.chat_message("assistant"):
                st.write(res["answer"])
                if res.get("chart"):
                    ch = res["chart"]
                    if ch["type"] == "heatmap":
                        cm3 = eda.correlation_matrix(df)
                        if cm3 is not None:
                            st.plotly_chart(charts.render_chart(df, "heatmap", corr=cm3), use_container_width=True)
                    else:
                        st.plotly_chart(charts.render_chart(df, ch["type"], ch.get("x"), ch.get("y")),
                                        use_container_width=True)
            st.session_state.qa.append({"q": q, "a": res["answer"], "chart": res.get("chart")})

    # ---- 报告 ----
    with tab4:
        md = report.build_markdown_report(st.session_state.active, prof, st.session_state.chart_specs, st.session_state.qa)
        st.markdown(md)
        st.download_button("⬇ 下载 Markdown 报告", md, file_name="DataPilot_分析报告.md", mime="text/markdown")


# ---------- router ----------
if st.session_state.page == "workspace" and valid_frames():
    render_workspace()
else:
    render_home()
