---
name: adjutant-memory-sync
description: 副官记忆仓自动同步 — 运行 perception.py --once 完成 git pull + 感知引擎 + push
---

# Adjutant Memory Sync

## Purpose
Automatically sync the hermes-adjutant repo: pull → perception engine → push.

## Command
```bash
cd /Users/mac/.hermes/profiles/her-m2/adjutant/repo/hermes-adjutant && python3 scripts/perception.py --once
```

## Fallback (if perception.py unavailable)
```bash
cd /Users/mac/.hermes/profiles/her-m2/adjutant/repo/hermes-adjutant
git pull origin main
git add -A
# commit only if diff is non-empty
git push origin main
```

## Output
- perception.py --once does: git fetch, advisor audit, optional telegram push
- Exit code 0 = success
- No local changes means nothing to push — this is normal
