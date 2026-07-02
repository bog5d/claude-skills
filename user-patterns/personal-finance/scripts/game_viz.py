#!/usr/bin/env python3
"""归途星火可视化生成器
Generate the 归途星火 HTML visualization from debts.json + config.json + game_state.json.
Usage: python3 game_viz.py
Output: ~/.hermes/cache/documents/return_starfire.html
"""

import json
import datetime
import os
from pathlib import Path

# Paths
SKILL_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
FINANCE_DIR = SKILL_DIR.parent.parent.parent.parent / "adjutant/repo/hermes-adjutant/finance"
FINANCE_DIR = FINANCE_DIR.resolve()

TEMPLATE_PATH = SKILL_DIR.parent / "templates/return_starfire.html"
OUTPUT_PATH = Path.home() / ".hermes/cache/documents/return_starfire.html"

# Load data
with open(FINANCE_DIR / "debts.json") as f:
    d = json.load(f)
with open(FINANCE_DIR / "config.json") as f:
    cfg = json.load(f)
with open(FINANCE_DIR / "game_state.json") as f:
    gs = json.load(f)

with open(TEMPLATE_PATH) as f:
    html = f.read()

grand = d["meta"]["grand_total"]
baseline = cfg["baseline_grand_total"]
cleared_total = d["meta"]["total_cleared"]

# Stats
html = html.replace("{{BASELINE}}", f"¥{baseline:,.0f}")
html = html.replace("{{CURRENT}}", f"¥{grand:,.0f}")
html = html.replace("{{PAID}}", f"¥{cleared_total:,.0f}")
html = html.replace("{{CLEARED_COUNT}}", f"{len(d['cleared'])} 盏")
html = html.replace("{{DATE}}", datetime.date.today().strftime("%Y-%m-%d"))

# Map milestones
milestones_html = ""
for m in cfg["milestones"]:
    th = m["threshold"]
    is_passed = grand <= th or any(
        e.get("threshold") == th
        for e in gs.get("events", [])
        if e.get("type") == "milestone"
    )
    mileage = max(grand - th, 0)
    status = "✅已到" if is_passed else f"差¥{mileage:,.0f}"
    milestones_html += f"""
    <div class="station-row">
        <span style="width:30px;font-size:16px">{m["icon"]}</span>
        <span style="flex:1;font-size:13px">{m["name"]}</span>
        <span style="font-size:12px;color:{"var(--green)" if is_passed else "var(--dim)"}">{status}</span>
        <span style="width:70px;text-align:right;font-size:14px;font-weight:700;color:var(--gold)">¥{th:,}</span>
    </div>"""

html = html.replace("{{MAP_SVG}}", milestones_html)

# Family rows (one per person, name first)
family = sorted(
    [x for x in d["active"] if x["type"] == "亲友"], key=lambda x: -x["amount"]
)
family_html = ""
for i, debt in enumerate(family):
    rank_class = f"top{i+1}" if i < 3 else ""
    rate_str = f'{debt["rate"]*100:.1f}%' if debt.get("rate") else ""
    note = (
        f'<span class="station-note">{debt.get("notes","")}</span>'
        if debt.get("notes")
        else ""
    )
    family_html += f"""
    <div class="station-row">
        <span class="station-rank {rank_class}">{i+1}</span>
        <span class="station-name">{debt["creditor"]}{note}</span>
        <span class="station-rate">{rate_str}</span>
        <div class="path-bar"><div class="path-fill mid" style="width:0%"></div></div>
        <span class="station-amount">¥{debt["amount"]:,}</span>
    </div>"""

html = html.replace("{{FAMILY_ROWS}}", family_html)
html = html.replace("{{FAMILY_COUNT}}", str(len(family)))

# Platform rows
platform = sorted(
    [x for x in d["active"] if x["type"] == "平台"], key=lambda x: -x["amount"]
)
plat_html = ""
for debt in platform:
    rate_str = f'{debt["rate"]}%' if debt.get("rate") else ""
    note = (
        f'<span class="station-note">{debt.get("notes","")[:40]}...</span>'
        if debt.get("notes")
        else ""
    )
    plat_html += f"""
    <div class="station-row">
        <span class="station-name" style="color:var(--blue)">{debt["creditor"]}{note}</span>
        <span class="station-rate">{rate_str}</span>
        <span class="station-amount">¥{debt["amount"]:,}</span>
    </div>"""

html = html.replace("{{PLATFORM_ROWS}}", plat_html)
html = html.replace("{{PLATFORM_COUNT}}", str(len(platform)))

# Starfire badges (cleared)
cleared_html = ""
for c in sorted(d["cleared"], key=lambda x: -x.get("original", 0)):
    is_legendary = c.get("original", 0) >= 100000
    amt = c.get("original", 0)
    cls = "starfire-badge legendary" if is_legendary else "starfire-badge"
    star = "✨ ✨" if is_legendary else "🏮"
    cleared_html += f"""
    <div class="{cls}">
        <div class="glow"></div>
        <div class="star">{star}</div>
        <div class="name">{c["creditor"]}</div>
        {f'<div class="amount">¥{amt:,}</div>' if amt else ""}
    </div>"""

html = html.replace("{{CLEARED_BADGES}}", cleared_html)

# Prediction
weekly_streak = gs.get("weekly_streak", 1)
achievements = len(gs.get("achievements_unlocked", {}))
prediction_html = f"""
<div class="predict-row">
    <div class="predict-icon">📊</div>
    <div class="predict-text">
        <div class="big">当前总负债 ¥{grand:,}</div>
        <div class="small">已践约 ¥{cleared_total:,} · 成就 {achievements}/8</div>
    </div>
    <div class="predict-value">零日约{round(grand/10000)}个月</div>
</div>
<div class="predict-row">
    <div class="predict-icon">🏆</div>
    <div class="predict-text">
        <div class="big">连胜{weekly_streak}周</div>
        <div class="small">连续记录</div>
    </div>
    <div class="predict-value">⛓️</div>
</div>"""

html = html.replace("{{PREDICTION_ROWS}}", prediction_html)

# Write output
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    f.write(html)

print(f"✅ 归途星火页面已生成: {OUTPUT_PATH}")
print(f"   总负债: ¥{grand:,}")
print(f"   已践约: ¥{cleared_total:,}")
print(f"   成就: {achievements}/8")
