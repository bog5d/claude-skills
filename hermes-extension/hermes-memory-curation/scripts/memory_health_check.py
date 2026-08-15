#!/usr/bin/env python3
"""Memory 健康检查 — 检查 MEMORY.md / USER.md 占用率，超过阈值时输出告警。

设计为 no_agent cron：无输出=安静（健康），有输出=需要整理。
"""
import re
from pathlib import Path

HOME = Path.home()
MEMORY_FILE = HOME / ".hermes" / "memories" / "MEMORY.md"
USER_FILE = HOME / ".hermes" / "memories" / "USER.md"

# 从 config.yaml 读取上限
import yaml
try:
    cfg = yaml.safe_load((HOME / ".hermes" / "config.yaml").read_text())
    mem_limit = cfg.get("memory", {}).get("memory_char_limit", 5000)
    user_limit = cfg.get("memory", {}).get("user_char_limit", 3000)
except Exception:
    mem_limit, user_limit = 5000, 3000

WARN_PCT = 80
CRIT_PCT = 90

def count_md(path):
    """统计 md 文件中的有效条目字符数（去掉 frontmatter 和 § 分隔符）"""
    try:
        text = path.read_text()
    except FileNotFoundError:
        return 0
    # 去 frontmatter
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2]
    # 去 § 分隔
    text = re.sub(r"^\s*§\s*$", "", text, flags=re.M)
    return len(text.strip())

mem_used = count_md(MEMORY_FILE)
user_used = count_md(USER_FILE)

mem_pct = mem_used / mem_limit * 100
user_pct = user_used / user_limit * 100

alerts = []
if mem_pct >= CRIT_PCT:
    alerts.append(f"🔴 MEMORY.md 已 {mem_pct:.0f}%（{mem_used}/{mem_limit}）— 必须立即整理：合并重复条目、把已沉淀技能的删掉")
elif mem_pct >= WARN_PCT:
    alerts.append(f"🟡 MEMORY.md 占用 {mem_pct:.0f}%（{mem_used}/{mem_limit}）— 建议整理：删除已进技能的内容，压缩旧条目")
if user_pct >= CRIT_PCT:
    alerts.append(f"🔴 USER.md 已 {user_pct:.0f}%（{user_used}/{user_limit}）— 必须立即整理")
elif user_pct >= WARN_PCT:
    alerts.append(f"🟡 USER.md 占用 {user_pct:.0f}%（{user_used}/{user_limit}）— 建议整理")

if alerts:
    print("📋 Memory 健康检查报告")
    for a in alerts:
        print(a)
    print(f"当前：MEMORY {mem_used}/{mem_limit} ({mem_pct:.0f}%) | USER {user_used}/{user_limit} ({user_pct:.0f}%)")
    print("整理原则：memory 只留48小时内活跃工作流+关键铁律；已沉淀进技能的删除；同类合并。")
