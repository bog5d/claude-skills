---
name: cross-profile-skills-sync
description: 为多个 Hermes profile 设置 skills 双向自动同步——每 N 分钟比较 mtime，较新的覆盖旧的，新 skill 自动拷贝，永不删除。
triggers:
  - "profile skills sync"
  - "跨 profile 同步 skills"
  - "两个 profile 互相学习"
  - "skills 双向同步"
---

# 跨 Profile Skills 双向同步

## 场景

用户有多个 Hermes profile（`default` 和 `her-m2`），每个 profile 有独立的 `skills/` 目录。希望所有 profile 的 skills 自动互相学习，且增量推送到 GitHub 供跨 AI 工具使用。

**四端同步路径（波总环境）：**
- SRC1: `~/.hermes/skills/` （当前 active profile her-m2）
- SRC2: `~/.hermes/profiles/her-m2/skills/` （her-m2 profile 冗余副本）
- SRC3: `~/.hermes/hermes-agent/skills/` （default profile 的技能目录）
- SRC4: `~/.hermes/profiles/english-tutor/skills/` （@Engcjd_bot 英语伴学 profile）

## 步骤

### 1. 创建三端同步脚本

脚本位置: `~/.hermes/scripts/sync_skills_cross_profile.sh`

**三阶段架构：**
- Phase 1: Tysk pull — 从 GitHub 拉最新 claude-skills + wangbo-brain
- Phase 2: 三端 mtime 比对 — 找最新版本，覆盖所有滞后端
- Phase 3: Tysk push — 本地 skills → rsync 进 claude-skills repo → git push GitHub

Phase 2 核心逻辑（三端比对）：
- 遍历四个目录的所有 SKILL.md
- 比较 mtime，找 newest（最晚修改的作为权威源）
- newest → 覆盖其余两端的旧版本
- 不删除任何 skill，只增加和更新

### 2. GitHub Push 关键配置

**⚠️ HTTPS push 必挂：** 大 repo（32MB, 468文件）用普通 HTTPS URL push 必超时。必须用 Token 认证 URL：
```bash
git remote set-url origin https://<token>@github.com/bog5d/claude-skills.git
```
SSH 未配置时此方案是唯一可行路径。

### 3. 首次运行验证

```bash
bash ~/.hermes/scripts/sync_skills_cross_profile.sh
# 确认三端数量一致
echo "her-m2: $(find ~/.hermes/skills -name SKILL.md -not -path '*/.git/*' | wc -l)"
echo "her-m2 profile: $(find ~/.hermes/profiles/her-m2/skills -name SKILL.md -not -path '*/.git/*' | wc -l)"
echo "default: $(find ~/.hermes/hermes-agent/skills -name SKILL.md -not -path '*/.git/*' | wc -l)"
echo "english-tutor: $(find ~/.hermes/profiles/english-tutor/skills -name SKILL.md -not -path '*/.git/*' | wc -l)"
```

### 4. 挂 cron job

```bash
cronjob create \
  --name "skills-sync-四端" \
  --schedule "every 30m" \
  --prompt "Execute bash ~/.hermes/scripts/sync_skills_cross_profile.sh. Report results." \
  --deliver local
```
⚠️ `deliver=local` 关键——避免每 30 分钟往 Telegram 推送同步日志。

## 实战教训

### ⚠️ GitHub push 卡了 32 天未发现
**根因：** 原脚本只有 Phase 1(Pull) + Phase 2(本地同步)，缺 Phase 3(Push)。另外 HTTPS push 在 32MB repo 上必定超时，需 Token URL。

**修复后验证：**
```bash
curl -s "https://api.github.com/repos/bog5d/claude-skills/commits/master" | python3 -c "import sys,json; print(json.load(sys.stdin)['commit']['message'][:80])"
```

### ⚠️ default profile 路径特殊
default profile 的 skills 不在 `~/.hermes/profiles/default/skills/`，而在 `~/.hermes/hermes-agent/skills/`（hermes-agent 源码内的 skills 目录）。必须在同步链中显式加入 SRC3。

### ⚠️ rsync --delete 会删 GitHub 仓库根文档
Phase 3 的 `rsync -a --delete "$SRC1/" ./` 会将仓库根目录所有不在 SRC1 里的文件删除——包括 README.md、AGENTS.md、SKILLS_SYNC_GUIDE.md。必须加 exclude：
```bash
rsync -a --delete --exclude='.git' --exclude='README.md' --exclude='AGENTS.md' --exclude='SKILLS_SYNC_GUIDE.md' "$SRC1/" ./
```

### ⚠️ rsync 不传 `--exclude='.git'` 会误删 .git 目录
如果从 non-git 源 rsync 到 git repo 目标，不加 `--exclude='.git'` 会删除目标的 .git 目录，后续 git push 无法工作。

## 限制

- 只在同一台机器上的 profile 间同步
- 不跨机器、不跨设备
- 跨设备同步通过 GitHub 仓库中转（Tysk 协议）
- HTTPS push 需要 Token URL，SSH 需提前配置好
