# -*- coding: utf-8 -*-
"""智能图表推荐与 plotly 渲染。供智能图表页与 AI 助手调用。"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import eda

VALID_TYPES = ["bar", "line", "scatter", "histogram", "box", "pie", "heatmap"]


@st.cache_data(show_spinner=False)
def recommend_charts(df):
    """根据列类型给出图表建议清单。"""
    profile = eda.profile_dataframe(df)
    recs = []
    num = profile["numeric"]
    cat = profile["categorical"]
    dt = profile["datetime"]

    if cat and num:
        recs.append({
            "type": "bar", "title": f"{cat[0]} 各分组平均 {num[0]}",
            "reason": f"类别列「{cat[0]}」配合数值列「{num[0]}」，适合看分组对比",
            "x": cat[0], "y": num[0],
        })
    if num:
        recs.append({
            "type": "histogram", "title": f"{num[0]} 分布",
            "reason": f"数值列「{num[0]}」用直方图看集中与离散",
            "x": num[0], "y": None,
        })
    if len(num) >= 2:
        recs.append({
            "type": "scatter", "title": f"{num[0]} vs {num[1]}",
            "reason": f"两数值列可看相关与离群点",
            "x": num[0], "y": num[1],
        })
    if dt and num:
        recs.append({
            "type": "line", "title": f"{dt[0]} 趋势 · {num[0]}",
            "reason": f"时间列「{dt[0]}」配合数值列看趋势",
            "x": dt[0], "y": num[0],
        })
    if cat and df[cat[0]].nunique() <= 10:
        recs.append({
            "type": "pie", "title": f"{cat[0]} 占比",
            "reason": f"类别「{cat[0]}」基数小，适合看构成",
            "x": cat[0], "y": None,
        })
    return recs


@st.cache_data(show_spinner=False)
def render_chart(df, chart_type, x=None, y=None, corr=None):
    """按类型渲染 plotly 图。corr 为相关性矩阵（heatmap 用）。"""
    chart_type = (chart_type or "").lower()
    if chart_type == "heatmap" and corr is not None:
        fig = go.Figure(data=go.Heatmap(
            z=corr.values, x=list(corr.columns), y=list(corr.index),
            colorscale="RdBu", zmid=0, text=corr.values,
            texttemplate="%{text}", colorbar=dict(title="相关系数"),
        ))
        fig.update_layout(height=460, margin=dict(l=40, r=20, t=20, b=40))
        return fig

    if chart_type == "bar":
        fig = px.bar(df, x=x, y=y, color=x if x in df.select_dtypes(include="object").columns else None)
    elif chart_type == "line":
        fig = px.line(df, x=x, y=y)
    elif chart_type == "scatter":
        fig = px.scatter(df, x=x, y=y)
    elif chart_type == "histogram":
        fig = px.histogram(df, x=x)
    elif chart_type == "box":
        fig = px.box(df, x=x, y=y)
    elif chart_type == "pie":
        vc = df[x].value_counts()
        fig = px.pie(values=vc.values, names=vc.index)
    else:
        fig = go.Figure()
        fig.add_annotation(text="暂不支持的图表类型", showarrow=False)
    fig.update_layout(height=460, margin=dict(l=40, r=20, t=20, b=40),
                      template="plotly_white", font=dict(family="Microsoft YaHei"))
    return fig
