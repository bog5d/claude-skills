---
name: adjutant-boot
description: 新会话启动标准流程——拉取副官系统最新状态。任何 AI（Hermes/Claude/Cursor/Copilot）接手波总任务时第一个执行。
category: user-patterns
trigger: session start, user asks about tasks/projects
priority: critical
---

# Adjutant Boot — 副官系统启动协议

## 目的
确保任何 AI 在新会话中立即获取波总全部任务的最新状态，无需用户重复说明。

## 触发条件
- 新会话启动时
- 用户询问"有什么任务""最近在做什么""项目状态"
- 用户说"记一下""记录下来"

## 执行步骤

### Step 1: 拉取副官仓库

```bash
cd ~/.hermes/adjutant/repo/hermes-adjutant
git pull origin main
```

如果仓库不存在，clone：
```bash
mkdir -p ~/.hermes/adjutant/repo
cd ~/.hermes/adjutant/repo
git clone https://github.com/bog5d/hermes-adjutant.git
```

### Step 2: 读取状态快照

```bash
cat status.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'总待办: {d[\"total_pending\"]} | 今日紧急: {d[\"today_urgent\"]} | 更新: {d[\"updated\"]}')"
```

### Step 3: 读取今日简报

```bash
cat brief/$(date +%Y-%m-%d).md 2>/dev/null || echo "今日无简报"
```

### Step 4: 列出待办任务（按优先级）

```python
import json
with open("status.json") as f:
    status = json.load(f)

critical = [t for t in status["tasks"] if t["priority"] == "critical"]
high = [t for t in status["tasks"] if t["priority"] == "high"]
medium = [t for t in status["tasks"] if t["priority"] == "medium"]

print("🔴 CRITICAL:")
for t in critical:
    print(f"  {t['id']} | {t['title']}")

print("🟠 HIGH:")
for t in high:
    print(f"  {t['id']} | {t['title']} | {t.get('date','')}")

print("🟡 MEDIUM:")
for t in medium:
    print(f"  {t['id']} | {t['title']}")
```

### Step 5: 向用户汇报（简洁）

只汇报关键信息：total pending、今日紧急、critical 任务。不要列全量清单除非用户要求。

---

## 操作后规则

任何任务状态变更后，立即执行：

```bash
cd ~/.hermes/adjutant/repo/hermes-adjutant
# 更新 status.json / tasks/active.json / tasks/completed.json
git add -A
git commit -m "<type>: <简短描述>"
git push origin main
```

commit 类型：
- `complete`: 标记任务完成
- `add`: 新增任务
- `update`: 更新任务信息
- `cancel`: 取消任务

---

## 跨 AI 工具使用

其他 AI 工具（Claude Code、Cursor、Copilot）同样适用：

1. `git clone https://github.com/bog5d/hermes-adjutant.git`
2. 读 `AGENTS.md`（本仓库的操作手册）
3. 读 `status.json`（当前状态）
4. 按 AGENTS.md 的规则操作

---

## 陷阱

- **不要靠 Hermes 的 memory 工具获取任务状态**——memory 容量有限且可能过期
- **不要靠 mem0 获取任务状态**——mem0 存储碎片化事实，不适合结构化任务列表
- **每次任务状态变更后必须立即 git push**——不等、不缓存
- **status.json 是单一事实源**——任何关于任务的判断都以它为准
