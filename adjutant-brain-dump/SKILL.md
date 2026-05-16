---
name: adjutant-brain-dump
description: 波总口语输入 → 结构化任务记录 → 同步到副官系统。当波总说"记一下""记录下来""有个任务"或描述要做的事时使用。
category: user-patterns
---

# 波总 Brain Dump → Adjutant 任务录入

## 触发条件
波总通过口语描述要做的事情，触发词包括："记下来""记录一下""有个任务""需要做"。

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

```python
import sqlite3, json, os
from pathlib import Path
from datetime import datetime

hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
db_path = hermes_home / "adjutant" / "db" / "adjutant.db"

# 获取下一个任务ID
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
existing = conn.execute("SELECT id FROM tasks ORDER BY id DESC LIMIT 1").fetchone()
max_num = int(existing["id"].lstrip("T")) if existing else 0
next_id = f"T{max_num + 1:03d}"

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

### 3. 同步到文件 + Git + 触发执行引擎
```bash
### 3. 同步到文件 + Git
```bash
python3 scripts/sync.py --push
```

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

## 示例
波总说："记一下，要让房东退款，给他发消息和费用结余图片"
→ T019 房东退款 | high | 行政 | 描述：发消息给房东+费用结余截图+要求退剩余租金
