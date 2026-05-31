# Gamification Output Templates

After every session (progressive or batch), append gamification output using these templates.

## State source
Read `~/.hermes/profiles/english-tutor/state/gamification.json` for streak/badge data.
Read `progress.json` snapshot for coverage/accuracy/rank.

## Badge definitions
```
first_blood:       🩸 第一滴血 — 完成首次挑战
streak_3:          🔥 三日连击 — 连续3天打卡
streak_7:          💥 七日不败 — 连续7天打卡
streak_14:         ⚡ 半月战神 — 连续14天打卡
streak_30:         👑 月度霸主 — 连续30天打卡
sharpshooter:      🎯 神枪手 — 单局正确率≥80%
perfect_game:      💎 完美一局 — 单局6/6全对
iron_will:         🏋️ 钢铁意志 — 断连击后重新连接
scholar_50:        📖 学徒 — 累计学习50词
scholar_100:       🎓 学者 — 累计学习100词
scholar_500:       📚 博学者 — 累计学习500词
progressive_first: ⚔️ 渐进先锋 — 完成渐进模式首通
batch_veteran:     🌊 一波流大师 — 完成5次Batch挑战
recovery_king:     🦅 涅槃重生 — 断连击后达成7天新连击
```

## Template: Session Complete

```
┌─────────────────────────────────────────────┐
│                                             │
│   ⚔️  {MODE} · SESSION {N} · 通关 ⚔️         │
│                                             │
│   斩杀 {correct}/{total}    命中率 {pct}%      │
│   {progress_bar}                            │
│                                             │
│   🏆 新解锁：{new_words}                     │
│   🔁 回炉×{count}：{review_words}            │
│   🔥 连击 ×{streak}  {streak_flame}          │
│                                             │
└─────────────────────────────────────────────┘
```

## Template: Gamification Panel

```
┌─────────────────────────────────────────────┐
│   🎮 游戏化面板                               │
│                                             │
│   🔥 连击  {streak}天   {streak_bar}          │
│   👑 最高  {longest}天                        │
│   🏆 徽章  {badge_icons}                     │
│   💰 +{xp} XP  (段位进度 {rank_bar})          │
│                                             │
│   📊 词库  {touched}/{total}   {coverage_bar} │
│   🎯 全局正确率  {accuracy}%                  │
│   🥉 段位  {rank}                            │
│                                             │
│   ⏭️ 下一徽章：{next_badge}                   │
└─────────────────────────────────────────────┘
```

## Progress bar function (inline Python)
```python
def bar(pct, w=16, fill="█", empty="░"):
    n = int(pct / 100 * w)
    return f"[{fill * n}{empty * (w-n)}] {pct:.0f}%"

def streak_flame(s):
    if s >= 30: return "👑"
    if s >= 14: return "⚡"
    if s >= 7:  return "💥"
    if s >= 3:  return "🔥"
    return "🕯️"
```

## New badge detection
After each session, re-evaluate all badge criteria. If any new badge is earned:
```
🎉 新徽章解锁！ {badge_icon} {badge_name}
   {badge_desc}
```

## Rank progression
```
🥉 青铜 → (100 words) → 🥈 白银 → (250) → 🥇 黄金 → (500) → 💎 铂金 → (800) → 👑 钻石 → (1100) → ⚔️ 王者 → (1331) → 🎓 考研战神
```

Show current rank + progress to next:
```
🥉 青铜  [██████░░░░░░░░░░░░░░]  42/100 → 🥈 白银
```

## Streak break alert
When streak resets after session due to >24h gap:
```
💀 连击断裂！
   上次：{old_streak}天 → 归零
   🏋️ 钢铁意志徽章已激活
   ⚔️ 重新开始，第1天！
```
