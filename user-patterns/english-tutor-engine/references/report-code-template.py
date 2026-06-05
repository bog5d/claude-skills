# 学习报告生成 — 工作版模板 (2026-06-05 实战验证)
# 
# 给定 words.json + progress.json + sessions.json (从 GitHub 拉取到 /tmp/vocab/),
# 此脚本生成完整学习报告，已修复所有已知公式/数据结构坑：
#   ✓ mastery 是 0-100 刻度，公式中除以 100 归一化
#   ✓ words.json["words"] 是 list，不是 dict
#   ✓ 正确率/连击从 history 字段重建，不信 snapshot
#   ✓ gamification.json 从本地 state/ 读取（不在 GitHub 上）
#   ✓ 已练词均值 ≠ 全库均值
#
# 用法: python3 /tmp/vocab/report.py

import json
from datetime import date

with open('/tmp/vocab/words.json') as f:
    words_data = json.load(f)
with open('/tmp/vocab/progress.json') as f:
    progress = json.load(f)

words = words_data["words"]  # ← LIST, not dict
total_words = len(words)

# === 已练词统计 ===
reviewed = [w for w in words if w.get("review_count", 0) > 0]
practiced_mastery_pct = sum(w.get("mastery", 0) for w in reviewed) / len(reviewed) if reviewed else 0
practiced_mastery_01 = practiced_mastery_pct / 100  # 归一化 for formulas
coverage_pct = len(reviewed) / total_words * 100

# === 正确率（从 history 重建，不信 snapshot）===
total_correct = 0
total_mistakes = 0
for w in words:
    for h in w.get("history", []):
        if h.get("result") == "correct":
            total_correct += 1
        elif h.get("result") == "wrong":
            total_mistakes += 1
total_answers = total_correct + total_mistakes
accuracy = total_correct / total_answers * 100 if total_answers else 0

# === 连击（从所有词 history 时间线重建）===
all_events = []
for w in words:
    for h in w.get("history", []):
        all_events.append((h.get("ts", ""), h.get("result", "")))
all_events.sort()
current_streak = 0
max_streak = 0
for _, result in all_events:
    if result == "correct":
        current_streak += 1
        max_streak = max(max_streak, current_streak)
    else:
        current_streak = 0

# === 学习局数 ===
sessions_count = len([h for h in progress.get("history", []) if isinstance(h, dict)])

# === 词库消化矩阵 ===
anki_w = [w for w in words if w.get("source") == "anki_import"]
preset_w = [w for w in words if w.get("source") == "preset_1500"]
anki_r = [w for w in anki_w if w.get("review_count", 0) > 0]
preset_r = [w for w in preset_w if w.get("review_count", 0) > 0]
anki_cov = len(anki_r) / len(anki_w) * 100 if anki_w else 0
preset_cov = len(preset_r) / len(preset_w) * 100 if preset_w else 0

# === 噩梦词 ===
nightmares = [w for w in words if w.get("nightmare_active")]

# === 预测分（mastery 归一化到 0-1 ）===
vocab_score = 25 + (coverage_pct / 100 * 0.4 + practiced_mastery_01 * 0.6) * 75

# === 达标预估 ===
if total_answers >= 10:
    gain_per_session = practiced_mastery_01 * 0.10
    if gain_per_session > 0 and vocab_score < 65:
        days_to_65 = int((65 - vocab_score) / gain_per_session)
    else:
        days_to_65 = 0
else:
    days_to_65 = None

# === Gamification（本地 state/ 目录）===
gam_path = "/Users/mac/.hermes/profiles/english-tutor/state/gamification.json"
try:
    with open(gam_path) as f:
        gam = json.load(f)
except:
    gam = {}

rank_map = {
    "bronze_i": "青铜I·入门者", "bronze_ii": "青铜II·积累者",
    "bronze_iii": "青铜III·突破者", "bronze_iv": "青铜IV·冲刺者",
    "silver": "白银"
}
sub_rank = gam.get("sub_rank", gam.get("rank", "bronze_i"))
total_score = gam.get("total_score", 0)
rank_progress = gam.get("rank_progress", 0)
rank_name = rank_map.get(sub_rank, str(sub_rank))

# === 错题（从 words history 提取）===
errors = []
for w in words:
    for h in w.get("history", []):
        if h.get("result") == "wrong":
            errors.append({
                "word": w.get("word", "?"),
                "resp": h.get("user_response", "?"),
                "ts": h.get("ts", "")
            })
errors.sort(key=lambda x: x["ts"], reverse=True)

# === 输出 ===
bar = lambda p: "▓" * int(p / 5) + "░" * (20 - int(p / 5))

print(f"📊 学习报告 — {date.today()}")
print(f"🏅 {rank_name}  |  ⭐{total_score}分  |  进度 {rank_progress}%")
print()
print(f"📈 已练: {len(reviewed)}/{total_words} ({coverage_pct:.1f}%) | 掌握率均值: {practiced_mastery_pct:.1f}%")
print(f"🎯 正确率: {total_correct}/{total_answers} ({accuracy:.1f}%) | 连击: {current_streak}/{max_streak} | 局数: {sessions_count}")
print()
print(f"📦 Anki: {len(anki_r)}/{len(anki_w)} {bar(anki_cov)} {anki_cov:.0f}%")
print(f"   1500: {len(preset_r)}/{len(preset_w)} {bar(preset_cov)} {preset_cov:.0f}%")
print()
phase = 1 if coverage_pct < 30 else 2
print(f"🎯 预测分: {vocab_score:.0f}/100 (Phase {phase}·仅词汇维度)" if phase == 1 else f"🎯 预测分: {vocab_score:.0f}/100 (Phase {phase}·词汇+阅读)")
if days_to_65 is not None and days_to_65 > 0:
    print(f"⏱ 达标(65分): ~{days_to_65}天")
if nightmares:
    print(f"👾 噩梦词: {len(nightmares)}个")
print()
if errors:
    print("📝 最近错题:")
    for e in errors[:5]:
        print(f"  {e['word']}: {e['resp']}")
    print()
if coverage_pct < 10:
    print("⚡ 优先扩面：每天≥12词冲10%覆盖率")
elif practiced_mastery_pct < 30:
    print("⚡ 集中复习：提升掌握率到30%+")
elif nightmares:
    print(f"⚡ 围剿{len(nightmares)}个噩梦词")
else:
    print("⚡ 节奏稳定：保持每日12词")
