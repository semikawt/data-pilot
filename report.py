# -*- coding: utf-8 -*-
"""分析报告生成（Markdown）。聚合画像、图表、问答亮点。"""


def build_markdown_report(name, profile, chart_specs, qa):
    """生成 Markdown 报告文本。"""
    lines = []
    lines.append(f"# 数据分析报告 · {name}")
    lines.append("")
    lines.append(f"> 由 DataPilot · AI 数据分析助手 自动生成")
    lines.append("")

    # 概况
    lines.append("## 一、数据集概况")
    lines.append(f"- 规模：**{profile['rows']} 行 × {profile['cols']} 列**")
    lines.append(f"- 数值列：{', '.join(profile['numeric']) or '无'}")
    lines.append(f"- 类别列：{', '.join(profile['categorical']) or '无'}")
    if profile["datetime"]:
        lines.append(f"- 时间列：{', '.join(profile['datetime'])}")
    lines.append("")

    # 数据质量
    miss = {c: profile["missing"][c] for c in profile["columns"] if profile["missing"][c] > 0}
    lines.append("## 二、数据质量")
    if not miss:
        lines.append("- 未检测到缺失值，完整度良好。")
    else:
        lines.append("- 缺失值明细：")
        for c, v in miss.items():
            lines.append(f"  - {c}：{v} 条（{profile['missing_pct'][c]}%）")
    lines.append("")

    # 关键指标
    if profile["describe"]:
        lines.append("## 三、关键指标（数值列）")
        lines.append("| 字段 | 均值 | 中位数 | 最小 | 最大 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for c, d in profile["describe"].items():
            lines.append(f"| {c} | {d['mean']} | {d['50%']} | {d['min']} | {d['max']} |")
        lines.append("")

    # 使用过的图表
    if chart_specs:
        lines.append("## 四、已探索的可视化")
        for i, c in enumerate(chart_specs, 1):
            title = c.get("title") or f"{c.get('type')}（{c.get('x')} / {c.get('y')}）"
            lines.append(f"{i}. {title}")
        lines.append("")

    # 问答亮点
    if qa:
        lines.append("## 五、分析问答记录")
        for item in qa:
            lines.append(f"**Q：{item['q']}**")
            ans = item['a'].replace("\n", "  \n")
            lines.append(f"A：{ans}  ")
            lines.append("")

    lines.append("---")
    lines.append("*本报告由数据自动生成，结论需结合业务进一步验证。*")
    return "\n".join(lines)
