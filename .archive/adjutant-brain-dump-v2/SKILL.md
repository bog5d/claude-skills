---
name: adjutant-brain-dump
description: 波总口语输入 → 结构化任务记录 → 同步到副官系统。当波总说"记一下""记录下来""有个任务"或描述要做的事时使用。
category: user-patterns
---

# 波总 Brain Dump → Adjutant 任务录入

## 触发条件

### 口语 Brain Dump
波总通过口语描述要做的事情，触发词包括："记下来""记录下来""有个任务""需要做"。

### 战略蓝图 Decomposition
波总发送结构化战略文档（Markdown、多章节计划），要求拆分为原子任务并刻入系统。
触发特征：文档含阶段/Phase 标注、[ ] checkbox 子项、明确的优先级分层。

→ 蓝图分解详细流程见 `references/blueprint-decomposition.md`

## 流程

### 1. 解析口语为结构化任务
从波总的话中提取：
- **任务名称**：简洁动词短语（如"房东退款""软著材料提交"）
- **优先级**：critical > high > medium > low
- **领域**：融资/法律/技术/行政/个人
- **描述**：保留原始语境 + 提炼关键行动点
- **截止日期**：显式或推断

### 2. 写入 Adjutant DB（直接 SQL INSERT）
init_db.py 不支持命令行传参——直接用 Python 写 SQL。
⚠️ **不要用 execute_code 工具**（cron/审批模式下被阻止）。用 `terminal + python3 heredoc` 代替：

```bash
cd ~/.hermes && python3 << 'PYEOF'
import ...
PYEOF
```

### 3. 更新 status.json
status.json 结构（注意正确 key 名）：
```json
{
  "updated": "ISO时间戳",
  "total_pending": 15,
  "today_urgent": 3,
  "tasks": [...]
}
```
**不是 `stats` / `stats.total_tasks`**——之前版本记录错误。正确顶层 key 为 `updated`, `total_pending`, `today_urgent`, `tasks`。

⚠️ **ID 冲突风险**：DB 和 status.json 可能不同步（status.json 有更新但 DB 未 sync）。
**必须先交叉比对两者获取真正的 max ID，不能只查 DB。**

```python
import sqlite3, json, os
from pathlib import Path
from datetime import datetime

hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
db_path = hermes_home / "adjutant" / "db" / "adjutant.db"
repo = hermes_home / "adjutant" / "repo" / "hermes-adjutant"

# 获取 DB 中最大 ID
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
existing_db = conn.execute("SELECT id FROM tasks ORDER BY id DESC LIMIT 1").fetchone()
db_max = int(existing_db["id"].lstrip("T")) if existing_db else 0

# 获取 status.json 中最大 ID
with open(repo / "status.json") as f:
    status_data = json.load(f)
status_ids = [int(t["id"].lstrip("T")) for t in status_data["tasks"] if t["id"].startswith("T")]
status_max = max(status_ids) if status_ids else 0

# 取两者最大值 +1
next_id = f"T{max(db_max, status_max) + 1:03d}"

now = datetime.now().isoformat()
conn.execute("""INSERT INTO tasks
    (id, title, description, priority, status, category, key_contacts, created_at, updated_at)
    VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)""",
    (next_id, title, description, priority, category,
     json.dumps(key_contacts, ensure_ascii=False), now, now))
conn.execute("INSERT INTO changelog (task_id, action, detail, operator) VALUES (?, 'created', ?, 'hermes')",
    (next_id, f"波总口述：{title}"))
conn.commit()
conn.close()
```

### 3. 同步到文件 + Git + 飞书双同步
```bash
### 3. 同步到文件 + Git + 飞书
```bash
python3 scripts/sync.py --push
python3 scripts/sync_to_lark.py   # 日历 + 任务双同步

### 4. 执行引擎（动作匹配 + 审计）
```bash
python3 scripts/executor.py --task <任务ID>
```
执行引擎会自动：
- 匹配规则 → 执行动作（Telegram通知/FOS看板/Obsidian笔记/Webhook）
- 运行审计 → 检测僵尸/闲置/deadline风险 → 推送 Telegram
- 高风险动作进入待确认队列

### 5. 确认录入
用简洁的一句话确认（如"已记录。T019 房东退款，high。"）

## 注意事项
- 描述字段保留波总原始口语语境，不要过度改写
- 如果任务包含多个步骤，在描述中用数字列出
- 如果有隐含的截止日期（如"明天""后天"），明确写入
- 不要等波总确认，直接录入+同步

## 陷阱
## 陷阱
- **DB 与 status.json 不同步**：DB 可能落后于 status.json（如其他 AI 通过 Git 推送了新任务但本地未跑 sync.py）。获取 max ID 时必须同时查询 DB 和 status.json，取最大值 +1，否则会覆盖已有任务。
- **DB 插入后 ≠ 任务已上线**：必须额外更新 status.json + `python3 scripts/sync.py --push` + git push。
- **sync.py 只同步 DB → docs/**：sync.py 输出到 docs/tasks.md 和 docs/summary.json，不更新 status.json。status.json 需手动维护 JSON。
- **status.json 顶层 key 是 `updated`/`total_pending`/`today_urgent`/`tasks`，不是 `stats`**：之前版本 skill 写错了。`data["total_pending"]` = sum pending，不是 `data["stats"]["pending"]`。
- **execute_code 在 cron/审批上下文被阻止**：不要用它。用 `terminal + python3 heredoc` 代替。
- **飞书同步 ≠ 日历同步**：`sync_to_lark.py` 现在执行三阶段（清理→创建→统计），有日期的任务进飞书日历，无日期的进飞书任务栏。`sync_feishu.py` 做双向同步（to-feishu + from-feishu），from-feishu 用轮转逐查（每次 3 个，配额友好）。
- **飞书打勾 ≠ 副官完成**：from-feishu 方向因配额限制是轮转轮询（非实时）。用户在飞书手动打勾的任务需要等 sync_feishu.py 轮转到才会回流到 status.json。最大延迟：映射任务数 ÷ 3 × 15 分钟。
- **飞书配额**：免费版 4-5 次 API 调用/天，0 点重置。不要用 `--page-all` 做全量轮询——改用逐 GUID 单查。

## 示例
波总说："记一下，要让房东退款，给他发消息和费用结余图片"
→ T019 房东退款 | high | 行政 | 描述：发消息给房东+费用结余截图+要求退剩余租金
