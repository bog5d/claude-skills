---
name: hermes-upgrade
description: 将 Hermes Agent 升级到最新版（从 GitHub 拉取 + 处理结构变更 + 重启 gateway）
---

# Hermes Agent 升级指南

将 Hermes Agent 从当前版本升级到 GitHub 最新版。

## 前置条件

- 本地有 git remote 指向 `https://github.com/NousResearch/hermes-agent.git`
- 当前在 `her-m2` 或其他 profile 下

## 升级步骤

### 1. 拉取最新代码

```bash
cd ~/.hermes/hermes-agent
git stash                          # 保存本地修改
git fetch origin
git reset --hard origin/main       # 远端分支是 main，不是 master
```

### 2. 清理旧文件残留

新版本可能删除了旧文件（如 `run_agent/_agent_monolith.py`），
git reset 不会自动删除这些本地独有文件：

```bash
git clean -fd                      # 删除未跟踪文件
```

### 3. 安装缺失依赖

新版本可能引入新依赖（如 `qrcode`, `certifi`）：

```bash
source venv/bin/activate
python -m pip install qrcode[pil]  # 按需安装
```

### 4. 验证核心模块

```bash
cd ~/.hermes/hermes-agent
source venv/bin/activate
python -c "import run_agent; print('OK')"
```

### 5. 重启 Gateway

```bash
# 查当前 gateway 进程
pgrep -f "hermes.*gateway"
# 杀掉旧进程（launchd 或 --replace 会自动重启）
kill <PID>
# 确认新进程已启动
pgrep -f "gateway run"
```

## 踩坑记录

| 问题 | 原因 | 解决 |
|------|------|------|
| `fatal: couldn't find remote ref master` | 远端主分支是 `main` 不是 `master` | 用 `origin/main` |
| `ModuleNotFoundError: No module named 'agent.activity'` | 旧文件 `_agent_monolith.py` 残留，新版本已删除该模块 | `git clean -fd` |
| 远端领先 5000+ 提交 | 正常，Hermes 活跃开发中 | 直接 reset hard，不需要 rebase |

## 后续

升级后建议跑全量测试：

```bash
cd ~/.hermes/hermes-agent
source venv/bin/activate
scripts/run_tests.sh
```
