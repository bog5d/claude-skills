# 战略蓝图批量任务拆解 (Blueprint → Tasks)

## 适用场景

波总发送结构化战略文档（非口语"记一下"），要求拆分为原子任务并刻入系统。

典型输入格式：
- Markdown 文档，含多阶段/多章节
- 每个章节有 [ ] checkbox 子项
- 可能带有优先级、依赖关系、阶段标记

## 处理流程

### Step 1: 解析文档结构

识别文档中的：
- **阶段/Phase 边界**：章节标题 → 作为任务分组的 phase 标签
- **任务节点**：每个 `[ ]` checkbox 或独立动作描述 → 一个原子任务
- **优先级信号**：阶段一=high/critical，后续阶段=medium，明确标注 critical 的单独提升
- **依赖关系**：顺次执行或可并行

### Step 2: 批量生成任务 ID

```python
# 从当前 status.json 获取 max ID，从 T040 开始递增
# 格式: T{max_id + 1:03d} 起，连续编号
```

### Step 3: 每个任务必须包含的字段

```json
{
  "id": "T040",
  "title": "认领/注册知乎账号（科技创投圈长尾搜索）",
  "status": "pending",
  "priority": "high",          // critical | high | medium | low
  "category": "个人监断",       // 与蓝图主题一致
  "date": "",
  "description": "缩略说明",
  "key_contacts": [],
  "claimed_by": "",
  "created_at": "<ISO 8601>",
  "updated_at": "<ISO 8601>"
}
```

### Step 4: 合并到 status.json

```python
with open("status.json") as f:
    status = json.load(f)

status["tasks"].extend(new_tasks)
status["total_pending"] = len([t for t in status["tasks"] if t["status"] == "pending"])
status["updated"] = datetime.now(tz).isoformat()

with open("status.json", "w") as f:
    json.dump(status, f, ensure_ascii=False, indent=2)
```

### Step 5: 提交 + Memory

```bash
git add status.json
git commit -m "add: <蓝图名称> - N项任务TXXX-TYYY"
git push origin main
```

```python
# memory add: 蓝图摘要 + 任务范围
# mem0_conclude: 完整上下文 + 战略意图
```

## 与口语 Brain Dump 的区别

| 维度 | 口语 Brain Dump | 蓝图 Decomposition |
|------|----------------|-------------------|
| 触发词 | "记一下" "记录下来" | 发送结构化 Markdown 文档 |
| 输入量 | 1-3 句话 | 整篇文档，多章节 |
| 任务数 | 通常 1 个 | 5-20 个 |
| 写入方式 | SQLite INSERT + sync.py | 直接操作 status.json + git push |
| 记忆深度 | memory add | memory add + mem0_conclude（战略级） |
| 分类 | 分散类别 | 统一 category（如"个人监断"） |

## 陷阱

- **不要走 SQLite INSERT 路径**：蓝图拆解是批量操作，走 status.json 直接写入更高效。口语 dump 的 DB → sync.py 路径不适合批量。
- **不要逐条汇报**：全部拆解完成后一次性汇报概要 + 按阶段分组清单，不要让波总逐条确认。
- **优先级对齐蓝图意图**：蓝图 Stage1=high，核心产出（如出道宣言）=critical，基础设施=medium。
- **category 统一**：蓝图任务共享同一 category（如"个人监断"），不要混入其他类别。
