---
name: adjutant-add-phase
description: 为副官系统新增一个 Phase/能力模块的标准流程。从架构设计到上线 cron 的完整 SOP。
category: user-patterns
triggers:
  - 波总说"把Q3干了""加一个XX引擎""副官要能XX"
  - 需要在 adjutant 系统中新增自动化能力
---

# 副官新增 Phase 标准流程

## 前置检查

```bash
cd ~/.hermes/adjutant/repo/hermes-adjutant
git pull origin main
cat status.json                    # 确认当前状态
cat AGENTS.md                      # 理解现有架构
ls scripts/                        # 看已有模块
```

## 设计原则

1. **遵循现有分层惯例**：每个 script 是一个独立 Phase，用 `--json` / `--dry-run` / `--once` 等统一 CLI 约定
2. **填充架构缺口**：先看现有 Phases 覆盖了什么，新 Phase 补什么
3. **三层层架构**（感知类模块）：
   - Sense Layer：从哪里获取信号（git/fetch, timer, file watcher）
   - Decide Layer：怎么判断要不要行动（规则匹配、阈值判断）
   - Act Layer：行动是什么（Telegram 推送、写文件、调 executor）

## 实现步骤

### 1. 创建脚本

路径：`~/.hermes/adjutant/repo/hermes-adjutant/scripts/<name>.py`

必须遵循的约定：
```python
#!/usr/bin/env python3
"""模块说明 + 用法示例"""

# ─── 路径配置（复用 adjutant 标准路径）───
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
ADJUTANT_HOME = HERMES_HOME / "adjutant"
DB_PATH = ADJUTANT_HOME / "db" / "adjutant.db"
REPO_DIR = ADJUTANT_HOME / "repo" / "hermes-adjutant"
TZ = timezone(timedelta(hours=8))

# ─── 环境变量加载（读 .env）───
def _load_env():
    env_path = ADJUTANT_HOME / ".env"
    ...

# ─── CLI 入口 ───
def main():
    _load_env()
    # 支持 --dry-run, --json, --once, --verbose 等
```

### 2. 测试

```bash
# 先 dry-run
python3 scripts/<name>.py --dry-run -v

# 再真跑一次
python3 scripts/<name>.py --once -v
```

### 3. 设置 cron

⚠️ **关键发现：macOS 上 crontab 命令经常超时/不可用。不要用系统 cron！**

用 Hermes 自带的 cronjob 工具：
```
cronjob action=create
  name="模块名称"
  schedule="*/5 * * * *"    # 或具体时间
  prompt="cd ~/.hermes/adjutant/repo/hermes-adjutant && python3 scripts/<name>.py --once"
  deliver="local"
```

### 4. 更新文档

更新 `AGENTS.md`：
- 在对应位置添加新 Phase 章节（含用法示例）
- 更新本地目录映射（`scripts/` 列表）
- 如果改变了启动流程，更新 START HERE 部分

### 5. 推送 + 记忆更新

```bash
git add scripts/<name>.py AGENTS.md
git commit -m "add: <Phase名> — <简短描述>"
git push origin main
```

然后用 `memory replace` 更新 adjutant 条目（注意 2,200 字符限制——合并旧条目而非新增）。

## 内存管理技巧

副官 memory 条目限制 2,200 字符。新 Phase 上线后：
- **替换**旧的 adjutant 条目，把新 Phase 合并进去
- 删除过时的 W 阶段记录
- 保持 adjutant 条目在 200 字符以内

## 已有 Phase 速查

| Phase | 脚本 | 功能 |
|-------|------|------|
| P1 | sync.py | db → 文件 → git push |
| P2 | night_shift.py | 凌晨预研 |
| P3 | handoff.py | 多 AI 交接 |
| P4 | query.py | 自然语言查询 |
| P5 | advisor.py | 风险预警 |
| P6 | executor.py | 规则匹配 + 自动执行 |
| Q3 | perception.py | 主动感知引擎（Git Sniffer + Chronos + Daemon） |
