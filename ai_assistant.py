# -*- coding: utf-8 -*-
"""对话式 AI 助手：有 LLM key 时调用大模型，否则规则兜底。安全不执行 LLM 生成代码。"""
import json
import os
import re

import pandas as pd

try:
    import streamlit as st
except Exception:
    st = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


# 配置优先级：页面「AI 接口设置」填写 > 环境变量 > Streamlit secrets
_UI_KEYS = {
    "OPENAI_API_KEY": "llm_api_key",
    "OPENAI_BASE_URL": "llm_base_url",
    "OPENAI_MODEL": "llm_model",
}


def _cfg(name, default=None):
    """统一读取配置：页面输入 > 环境变量 > Streamlit secrets > 默认值。"""
    if st is not None:
        try:
            v = st.session_state.get(_UI_KEYS.get(name, ""))
            if v:
                return v
        except Exception:
            pass
    v = os.environ.get(name)
    if v:
        return v
    if st is not None:
        try:
            v = st.secrets.get(name)
            if v:
                return v
        except Exception:
            pass
    return default


def llm_configured():
    """是否已配置可用的 LLM。"""
    return bool(_cfg("OPENAI_API_KEY")) and OpenAI is not None


def _client():
    key = _cfg("OPENAI_API_KEY")
    base = _cfg("OPENAI_BASE_URL")
    kwargs = {"api_key": key}
    if base:
        kwargs["base_url"] = base
    return OpenAI(**kwargs)


def _profile_text(profile):
    lines = [f"数据集：{profile['rows']} 行 × {profile['cols']} 列。", "字段："]
    for c in profile["columns"]:
        lines.append(f"  - {c}（{profile['kinds'][c]}）")
    if profile["describe"]:
        lines.append("数值列统计：")
        for c, d in profile["describe"].items():
            lines.append(f"  - {c}: 均值 {d['mean']}，中位数 {d['50%']}，最大 {d['max']}，最小 {d['min']}")
    return "\n".join(lines)


def answer_question(df, profile, question, history=None):
    """返回 {'answer': str, 'chart': {type,x,y}|None, 'source': 'llm'|'rule'}。"""
    q = (question or "").strip()
    if not q:
        return {"answer": "请输入你的问题。", "chart": None, "source": "rule"}

    if llm_configured():
        try:
            return _llm_answer(df, profile, q, history or [])
        except Exception as e:
            # LLM 失败优雅降级到规则，保证产品可用
            rule = _rule_answer(df, profile, q)
            rule["answer"] = f"（AI 接口异常，已切换本地分析）{rule['answer']}"
            return rule

    return _rule_answer(df, profile, q)


def _llm_answer(df, profile, question, history):
    client = _client()
    model = _cfg("OPENAI_MODEL", "gpt-4o-mini")
    system = (
        "你是一个数据分析助手。下面给出数据集结构。请回答用户问题，"
        "并以 JSON 返回：{\"answer\": 中文分析文本, \"chart\": "
        "{\"type\": \"bar|line|scatter|histogram|box|pie|heatmap\"|null, "
        "\"x\": 列名|null, \"y\": 列名|null}}。"
        "chart 仅在问题明显需要可视化时给出，且 x/y 必须是真实存在的列名。"
        "不要编造不存在的列。\n\n" + _profile_text(profile)
    )
    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:
        messages.append({"role": "user", "content": h.get("q", "")})
        messages.append({"role": "assistant", "content": h.get("a", "")})
    messages.append({"role": "user", "content": question})

    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=0.2,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    data = json.loads(content)
    chart = _validate_chart(df, data.get("chart"))
    return {
        "answer": data.get("answer", "（无回答）"),
        "chart": chart,
        "source": "llm",
    }


def _validate_chart(df, chart):
    if not isinstance(chart, dict):
        return None
    t = (chart.get("type") or "").lower()
    if t not in ("bar", "line", "scatter", "histogram", "box", "pie", "heatmap"):
        return None
    x, y = chart.get("x"), chart.get("y")
    if x and x not in df.columns:
        x = None
    if y and y not in df.columns:
        y = None
    if t in ("heatmap",):
        return {"type": "heatmap", "x": None, "y": None}
    if t in ("histogram", "pie") and not x:
        return None
    if t in ("bar", "line", "scatter", "box") and not x:
        return None
    return {"type": t, "x": x, "y": y}


def _rule_answer(df, profile, question):
    q = question.lower()
    cols = profile["columns"]
    num = profile["numeric"]
    cat = profile["categorical"]

    # 缺失 / 数据质量
    if any(k in q for k in ["缺失", "空值", "空", "质量", "完整"]):
        miss = {c: profile["missing"][c] for c in cols if profile["missing"][c] > 0}
        if not miss:
            return {"answer": "未检测到缺失值，数据完整度良好。", "chart": None, "source": "rule"}
        txt = "缺失值情况：\n" + "\n".join(
            f"  - {c}：{v} 条（{profile['missing_pct'][c]}%）" for c, v in miss.items()
        )
        return {"answer": txt, "chart": None, "source": "rule"}

    # 相关性
    if any(k in q for k in ["相关", "关系", "corr", "影响"]):
        corr_cols = [c for c in num if df[c].nunique(dropna=True) > 1]
        if len(corr_cols) >= 2:
            cm = df[corr_cols].corr().abs().unstack().sort_values(ascending=False)
            seen, pairs = set(), []
            for (a, b), v in cm.items():
                if a == b:
                    continue
                key = tuple(sorted((a, b)))
                if key in seen:
                    continue
                seen.add(key)
                pairs.append(f"{a} ↔ {b}：{round(float(v), 2)}")
                if len(pairs) >= 3:
                    break
            return {
                "answer": "相关性最强的前几对（绝对值）：\n" + "\n".join(f"  - {p}" for p in pairs),
                "chart": {"type": "heatmap", "x": None, "y": None},
                "source": "rule",
            }
        return {"answer": "数值列不足，无法计算相关性。", "chart": None, "source": "rule"}

    # Top / 最大 / 最高
    m = re.search(r"(最高|最大|top|前\d+|top\d+)\s*(\w+)?", q)
    if (any(k in q for k in ["最高", "最大", "top", "前"]) and num) or m:
        target = None
        for c in num:
            if c.lower() in q or c in q:
                target = c
                break
        target = target or num[0]
        top = df.nlargest(5, target)[[target] + (cat[:1] if cat else [])].drop_duplicates()
        lines = [f"按「{target}」降序 Top5："]
        for _, r in top.iterrows():
            lines.append("  - " + "，".join(f"{k}={r[k]}" for k in top.columns))
        return {"answer": "\n".join(lines), "chart": None, "source": "rule"}

    # 分布 / 直方图
    if any(k in q for k in ["分布", "直方图", "离散"]):
        t = num[0] if num else None
        if t:
            return {"answer": f"「{t}」的分布可用直方图查看。", "chart": {"type": "histogram", "x": t, "y": None}, "source": "rule"}

    # 趋势
    if any(k in q for k in ["趋势", "变化", "走势"]) and profile["datetime"] and num:
        t, x = num[0], profile["datetime"][0]
        return {"answer": f"「{x}」上「{t}」的趋势可用折线图查看。", "chart": {"type": "line", "x": x, "y": t}, "source": "rule"}

    # 默认：概览总结
    summary = (
        f"该数据集共 {profile['rows']} 行、{profile['cols']} 列。"
        f"数值列 {len(num)} 个（{', '.join(num) or '无'}），"
        f"类别列 {len(cat)} 个（{', '.join(cat) or '无'}）。"
    )
    miss_total = sum(profile["missing"].values())
    if miss_total:
        summary += f"存在 {miss_total} 个缺失值，可在「数据概览」查看明细。"
    summary += "你可以问我：缺失情况、相关性、Top 排行、分布或趋势。"
    return {"answer": summary, "chart": None, "source": "rule"}
