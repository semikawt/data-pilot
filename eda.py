# -*- coding: utf-8 -*-
"""数据接入与自动画像（EDA）。被首页、概览页、AI 助手、报告复用。"""
import io
import numpy as np
import pandas as pd
import streamlit as st


def load_dataframes(uploaded_files):
    """上传的 Streamlit UploadedFile 列表 -> {文件名: DataFrame}。"""
    frames = {}
    for f in uploaded_files or []:
        name = f.name
        try:
            if name.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(f)
            else:
                df = pd.read_csv(f)
            frames[name] = df
        except Exception as e:  # 解析失败跳过该文件，不阻断其它
            frames[name] = f"读取失败：{e}"
    return frames


@st.cache_data(show_spinner=False)
def get_sample_data():
    """内置离线样例：一份模拟销售明细，便于零数据也能体验产品。"""
    rng = np.random.default_rng(42)
    n = 240
    regions = rng.choice(["华北", "华东", "华南", "西部"], n, p=[0.3, 0.35, 0.25, 0.1])
    channels = rng.choice(["线上", "门店", "代理"], n, p=[0.5, 0.35, 0.15])
    dates = pd.date_range("2026-01-01", periods=n, freq="D").to_series().reset_index(drop=True)
    sales = np.maximum(0, rng.normal(5200, 1800, n) + (regions == "华东") * 900)
    orders = np.maximum(1, (sales / rng.uniform(180, 320, n)).astype(int))
    repurchase = (rng.random(n) < 0.28).astype(int)
    df = pd.DataFrame({
        "日期": dates,
        "地区": regions,
        "渠道": channels,
        "销售额": sales.round(2),
        "订单数": orders,
        "客单价": (sales / orders).round(2),
        "是否复购": repurchase,
    })
    # 人为制造少量缺失，展示数据质量能力
    miss_idx = rng.choice(n, 12, replace=False)
    df.loc[miss_idx, "客单价"] = np.nan
    return df


def _col_kind(df, col):
    dt = df[col].dtype
    if pd.api.types.is_datetime64_any_dtype(dt):
        return "datetime"
    if pd.api.types.is_numeric_dtype(dt):
        return "numeric"
    nunique = df[col].nunique(dropna=True)
    if nunique <= 30:
        return "categorical"
    return "text"


@st.cache_data(show_spinner=False)
def profile_dataframe(df):
    """生成数据画像字典，供概览 / AI 助手 / 报告复用。"""
    kinds = {c: _col_kind(df, c) for c in df.columns}
    numeric = [c for c, k in kinds.items() if k == "numeric"]
    categorical = [c for c, k in kinds.items() if k == "categorical"]
    datetime_cols = [c for c, k in kinds.items() if k == "datetime"]

    missing = {c: int(df[c].isna().sum()) for c in df.columns}
    missing_pct = {c: round(100 * df[c].isna().mean(), 1) for c in df.columns}

    describe = {}
    if numeric:
        desc = df[numeric].describe().T
        describe = {
            c: {
                "mean": round(float(desc.loc[c, "mean"]), 2),
                "std": round(float(desc.loc[c, "std"]), 2),
                "min": round(float(desc.loc[c, "min"]), 2),
                "50%": round(float(desc.loc[c, "50%"]), 2),
                "max": round(float(desc.loc[c, "max"]), 2),
            }
            for c in numeric
        }

    return {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "columns": list(df.columns),
        "kinds": kinds,
        "numeric": numeric,
        "categorical": categorical,
        "datetime": datetime_cols,
        "missing": missing,
        "missing_pct": missing_pct,
        "describe": describe,
        "head": df.head(5),
    }


@st.cache_data(show_spinner=False)
def correlation_matrix(df, numeric_cols=None):
    """返回数值列相关性矩阵（DataFrame），无数值列返回 None。"""
    cols = numeric_cols or [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cols = [c for c in cols if df[c].nunique(dropna=True) > 1]
    if len(cols) < 2:
        return None
    return df[cols].corr(numeric_only=True).round(2)
