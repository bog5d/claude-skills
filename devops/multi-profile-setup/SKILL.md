---
name: multi-profile-setup
description: 为 Hermes 创建多线并行工作环境——独立 profile + Telegram bot + skills 双向同步。适用场景：波总说"开一条新工作线""绑另一个 bot""两个 Hermes 同时做不同事"。
trigger:
  - 开新工作线
  - 多 profile
  - 另一个 bot
  - 第二个 bot
  - 分开工作
  - 多线并行
---

# Multi-Profile Setup — 多线并行工作环境

## 概述

创建完全隔离的 Hermes profile，绑定独立 Telegram bot，设置定时 skills 双向同步，实现 A 线/B 线并行工作。

---

## Phase 1: 创建 Profile

```bash
# 创建新 profile（克隆当前配置和 API keys）
hermes profile create <name> --clone

# <name> 限制: [a-z0-9][a-z0-9_-]{0,63}，不能有大写字母
```

创建后自动生成快捷命令 `<name>`（如 `her-m2 chat`）。

---

## Phase 2: 配置独立 Bot Token

1. 去 @BotFather 创建新 bot，拿到 token
2. 替换 .env 中的 TELEGRAM_BOT_TOKEN：

```bash
# ⚠️ 必须用 terminal sed 而非 patch 工具
# 因为 credential 保护机制会替换读取内容为占位符
sed -i '' 's/^TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=<新token>/' ~/.hermes/profiles/<name>/.env

# 验证 token 已正确写入（字符数校验）
grep 'TELEGRAM_BOT_TOKEN' ~/.hermes/profiles/<name>/.env | wc -c
# 应等于 TELEGRAM_BOT_TOKEN=(19) + token长度 + 1(换行符)
```

**Pitfall:** patch 工具读取文件时可能看到 credential 占位符而非真实内容，导致匹配失败。必须用 terminal sed 操作。

---

## Phase 3: 启动 Gateway

```bash
HERMES_HOME=~/.hermes/profiles/<name> hermes gateway start
```

验证两个 profile 都在运行：
```bash
hermes profile list
```

---

## Phase 4: Skills 双向同步

创建同步脚本，挂到 cron 每 30 分钟运行。

### 同步脚本核心逻辑

```bash
# 双向合并: mtime 较新者胜，不删除任何文件
# SRC1: ~/.hermes/skills/
# SRC2: ~/.hermes/profiles/<name>/skills/

for skill in (两边所有 skill 目录); do
    if 两边都存在:
        比较 SKILL.md mtime → 新的覆盖旧的
    elif 只在一边:
        拷贝到另一边
    永不删除
done
```

### Cron 配置

```bash
# 用 cronjob tool 创建定时任务
cronjob create \
  --schedule "every 30m" \
  --deliver local \
  --prompt "运行 bash ~/.hermes/scripts/sync_skills_cross_profile.sh，完成后回复 skills synced"
```

---

## 验证清单

- [ ] `hermes profile list` 显示两个 profile，gateway 均在运行
- [ ] 两个 bot 在 Telegram 上都能响应
- [ ] 运行一次同步脚本确认两边 skills 数量一致
- [ ] 查看 cron 确认定时任务已调度
