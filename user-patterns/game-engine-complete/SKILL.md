---
name: game-engine-complete
description: 波总 Vocab Tracker 完整游戏化引擎 — 闯关循环、进度环、里程碑、连击宝箱、Boss战、晋升公告、子里程碑、道具系统
---

# Game Engine — 完整闯关引擎 v3

## 核心约束（从用户反馈中提取）

- **响应速度铁律**：全部数据操作（SM-2 + GitHub push + 下轮词预取 + 讲解预生成）必须在 1 次 `terminal()` 调用内完成。**当前标准路径**：`session_pipeline.py` 一次性处理判分→SM-2→五层→gamification→push。LLM 不再手写 execute_code。
- **判分结论显性化**：判分结果放在最前面并用分隔线焊死，不能被 5 层讲解淹没。
- **每词必出完整 5 层讲解**：词根拆解+演化链+视觉锚点+原卡背景+考研锚，答对答错都出。session_pipeline.py 的 FIVE_LAYER 字典已内置 27 词全库。

## 架构

```
用户答完 → terminal: session_pipeline.py <round> '<answers>'
         → 脚本输出 JSON（含 _formatted 字段）
         → LLM relay 输出 + MEDIA 投递（如有 chronicle）
```

## config.json 新增模块

### milestones
8 级里程碑：5/10/20/50/100/200/500/1000 词。每级有名称/奖励分/解锁能力。已通过 `unlocks` 映射关联。

### boss
- boss_pool: 20 个超纲词
- boss_hp: 3
- summon_interval: 每 10 次正确召唤 1 个
- reward_points: 50
- taunts/defeat_messages: 随机文本池
- 击败：记录到 bosses_defeated + 发放徽章

### boss_items
4 种道具：
- 🔍 词根透镜 (common) — 揭示词根，让用户猜方向
- 📋 选择护盾 (common) — 4 选 1 选择题
- ⏸️ 冻结药剂 (rare) — 跳过 Boss 回合
- ⚡ 双倍连击 (rare) — 1 次正确 = 2 点伤害
- earn_interval: 每 5 次正确获得 1 个道具
- initial_grant: 新手礼包 2x 透镜 + 1x 护盾
- drop_chance_on_boss_defeat: 50% Boss 掉落

⚠️ 关键规则（用户验证）：词根透镜 + 选择护盾 不能同时使用——叠加效果会让答题变得毫无挑战。一次只能用 1 个道具。

### rank_promotion
6 个段位晋升主题，每个有标题/描述/颜色。晋升时自动加 80 分。

### sub_milestones
每 3 词触发一次小里程碑（3/6/9/12……30）。每步有小标题（小步快跑/渐入佳境）和 5-25 分奖励。首次启动时可能同时触发多个——在 engine 里只保留最高一个。

### daily_report
cron job：每天 9:00 发送日报。包含快照/进度环/今日单词/Boss状态/毒鸡汤。

### unlocked_modes
8 种可解锁能力：progress_bar / streak_chest / reverse_mode / synonym_mode / root_tree / mock_test / lord_bonus / full_prediction。
通过 milestones + unlocks 映射关联，milestone 达成后自动解锁。

## progress.json 新增字段

```json
{
  "snapshot": { "...": "...", "total_correct_all_time": 13 },
  "milestones_reached": [1, 2, 3],
  "boss_state": {
    "current_boss": {"word": "preposterous", "hp": 2, "max_hp": 3},
    "bosses_defeated": ["obsolete"],
    "boss_damage_dealt": 4,
    "next_boss_at": 20
  },
  "unlocked_modes": ["progress_bar", "streak_chest", "reverse_mode"],
  "inventory": {
    "root_lens": 2, "choice_shield": 0, "freeze_potion": 0, "double_strike": 0,
    "items_earned_total": 3, "items_used_total": 1
  },
  "collection": {
    "bonus_words_conquered": [],
    "total_bonus_earned": 0
  },
  "sub_milestone_tracker": {
    "reached": [21, 24]
  }
}
```

## 进度条生成

20 个 Unicode 字符，三段：
- 覆盖 ▏█░░░░░░░░░░░░░░░░░░░░▏1.8%
- 掌握 ▏█████░░░░░░░░░░░░░░░▏25.0%
- 晋段 ▏███████████░░░░░░░░░▏52.4% → 白银

## 连击火焰系统（2026-06-06 上线）

`gamification_v2.gen_panel()` 内置，对标 Duolingo Streak Freeze：
- 0-2天：🔥
- 3-6天：🔥🔥🔥
- 7-13天：🔥🔥🔥🔥🔥⚡ ON FIRE
- 14+天：🔥🔥🔥🔥🔥🔥🔥🌈 LEGENDARY

## 交付模式（2026-06-06 用户纠正 ⚠️ 铁律）

**不要发 MEDIA 文件碎片。** Session 结束后只发 **1 个公网 URL**：
- `{tunnel_url}/chronicle_index.html` — 点开全部页面可导航
- URL 由 `state/tunnel_daemon.py` 守护 HTTP server + SSH 隧道
- `session_pipeline.py` 输出自动注入 `tunnel_url` 字段
- `_formatted` 输出自带 URL 行：`🌐 **实时档案馆**: {url}/chronicle_index.html`
- 用户原话：「不是发 MEDIA 碎片，约定的是一个网址」

勋章收藏室 (`chronicle_index.html`) 顶部新增「📊 战报中心」：
- 📊 周战报 → `state/weekly_report.html`（Strava Weekly Recap 风格）
- 🎯 弱点雷达 → `state/weakness_radar.html`（Khan Academy Mastery 风格 SVG）
- 📸 战绩分享卡 → `state/share_card.html`（Zwift Ride Summary 风格）

生成器：`state/weekly_report.py` + `state/weakness_share.py`。周日 health_monitor 自动触发。

## Tier 2 能力系统（2026-06-06 上线）

勋章收藏室新增「🌳 Tier 2 · 新能力」按钮区，4 项独立 HTML 页面：

| 能力 | 脚本 | 对标 | 说明 |
|------|------|------|------|
| **技能树** | `state/skill_tree.py` | Habitica | 25 技能 × 7 段位，暗黑 HTML，已解锁金色发光+动画 |
| **噩梦词通缉令** | `state/nightmare_wanted.py` | Monster Hunter | WANTED 海报，SSS~E 评级，含犯罪证据+赏金 XP |
| **季节叙事** | `state/season_narrative.py` | Fortnite | 5 季 Battle Pass，按段位解锁，含赛季任务 |
| **成就系统** | `state/achievement_system.py` | Xbox | 22 成就 × 5 稀有度，Gamerscore 体系 |

**开发模式**：所有 Tier 2 脚本独立运行，遵循 `weekly_report.py` 模式——`_get_token()`（git config）+ `_fetch()`（GitHub API）+ 生成 HTML。不依赖 session_pipeline.py 的答题流程。

**注册**：`chronicle_index_generator.py` 已追加 4 个 Tier 2 入口链接，位于「📊 战报中心」下方。

## 常见坑

1. **子里程碑洪水**：首次启动时从 step(3) 到 max_word(30) 的循环会触发所有跨越过的阈值。修复方案：启动时只保留最高值，后续逐级触发。
2. **解锁能力初始化**：已达成的 milestone 对应的 unlock 必须在启动时 auto-populate，不能等新 milestone 触发才解锁。
3. **total_correct_all_time 初始化**：必须从 history 中统计已有正确次数，不能从 0 开始。
4. **Boss 生存期**：Boss 跨 round 存活——每次答对扣 1 HP，不是每轮扣 1。
5. **item earn_interval**：需要用 `while earned < should_have` 循环补发，不能只判断一次。
6. **不要 clone 整个 repo**：GitHub API 直取单个 JSON 文件，约 600KB。Python urllib 可能被截断——沙箱内用 execute_code 的 urllib 加 SSL 兼容。
7. **Aider bridge 不可用于 english-tutor 开发**：`bridge_cmd.py` 硬绑 Cangjie 路径，english-tutor 脚本直接手写。
8. **Telegram Bot Token 被过滤器截断**：`write_file`/`execute_code` 中含 `TELEGRAM_BOT_TOKEN=*** 的行会被截断。发送文件到 Telegram 必须用 shell 变量 + curl。
