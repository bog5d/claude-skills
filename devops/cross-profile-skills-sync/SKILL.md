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

用户有多个 Hermes profile（如 `default` 和 `her-m2`），每个 profile 有独立的 `skills/` 目录。希望两边的 skills 自动互相学习——任何一个 profile 中学到的 skill，另一个也能用上。

## 步骤

### 1. 创建同步脚本

脚本位置: `~/.hermes/scripts/sync_skills_cross_profile.sh`

脚本逻辑：
- 遍历两个目录的所有 SKILL.md
- 两边都有的：比较 mtime，较新的用 `rsync -a --delete` 覆盖旧的
- 只在一边的：rsync 到另一边
- 不删除任何 skill，只增加和更新
- 日志写 `~/.hermes/logs/sync_skills.log`

关键实现细节：
- `stat -f %m` (macOS) / `stat -c %Y` (Linux) 兼容
- `find ... -not -path '*/.git/*' -not -path '*/.hub/*'` 排除 git 和 hub 目录
- 用 `rsync` 保证目录完整性（以 `/` 结尾拷贝目录内容）

### 2. 首次运行验证

```bash
bash ~/.hermes/scripts/sync_skills_cross_profile.sh
cat ~/.hermes/logs/sync_skills.log
# 确认两边数量一致
find ~/.hermes/skills -name SKILL.md -not -path '*/.git/*' | wc -l
find ~/.hermes/profiles/her-m2/skills -name SKILL.md -not -path '*/.git/*' | wc -l
```

### 3. 挂 cron job

使用 `cronjob` tool，`deliver=local` 避免每 30 分钟推送一条到聊天。

## 脚本模板

```bash
#!/bin/bash
set -euo pipefail

SRC1="$HOME/.hermes/skills"
SRC2="$HOME/.hermes/profiles/<profile-name>/skills"
LOG="$HOME/.hermes/logs/sync_skills.log"

mkdir -p "$(dirname "$LOG")"

log() { echo "[$(date)] $*" >> "$LOG"; }

find_skills() {
    find "$1" -name "SKILL.md" -not -path "*/.git/*" -not -path "*/.hub/*" 2>/dev/null \
        | sed "s|/SKILL.md$||" | sed "s|^$1/||" | sort -u
}

log "=== Sync started ==="

updated=0; copied=0

while IFS= read -r skill; do
    d1="$SRC1/$skill"; d2="$SRC2/$skill"

    if [ -d "$d1" ] && [ -d "$d2" ]; then
        t1=$(stat -f %m "$d1/SKILL.md" 2>/dev/null || stat -c %Y "$d1/SKILL.md" 2>/dev/null || echo 0)
        t2=$(stat -f %m "$d2/SKILL.md" 2>/dev/null || stat -c %Y "$d2/SKILL.md" 2>/dev/null || echo 0)

        if [ "$t1" -gt "$t2" ]; then
            rsync -a --delete "$d1/" "$d2/"
            log "  <- SRC1 -> SRC2: $skill"
            updated=$((updated + 1))
        elif [ "$t2" -gt "$t1" ]; then
            rsync -a --delete "$d2/" "$d1/"
            log "  <- SRC2 -> SRC1: $skill"
            updated=$((updated + 1))
        fi
    elif [ -d "$d1" ]; then
        rsync -a "$d1/" "$d2/"
        log "  + SRC1 -> SRC2: $skill"
        copied=$((copied + 1))
    elif [ -d "$d2" ]; then
        rsync -a "$d2/" "$d1/"
        log "  + SRC2 -> SRC1: $skill"
        copied=$((copied + 1))
    fi
done < <( { find_skills "$SRC1"; find_skills "$SRC2"; } | sort -u )

log "Done — updated: $updated, copied: $copied"
```

## 限制

- 只在同一台机器上的两个 profile 间同步
- 不跨机器、不跨设备
- 如需跨设备同步，改用 GitHub 仓库中转（参见 Tysk 协议）
