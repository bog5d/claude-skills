---
name: context-compression-layer-upgrade
title: "Context Compression 三层升级工作流"
description: "Hermes Agent 的 context_compressor 升级——StagedArchiver + 知识指纹 + /uncompress 回溯 + 前瞻检测。包含 schema 迁移、SQLite 存档、slash command 注册等完整模式。"
trigger: "用户要求升级上下文压缩策略（三层压缩、压缩存档、/uncompress 回溯）时"
---

## 架构总览

```
hermes_state.py (schema v7)
  └─ compressed_archives 表
       ├─ session_id, compression_round, archived_at
       ├─ summary_text — LLM 摘要
       ├─ knowledge_fingerprint — 结构化知识提取（JSON）
       ├─ n_messages, n_tokens_saved
       └─ messages_json — 完整原始消息 JSON

agent/context_compressor.py
  ├─ session_db 参数 → SQLite 存档
  ├─ _extract_knowledge_fingerprint() — 正则提取文件路径/命令/键值/工具名
  ├─ _token_history / _lookahead_triggered → 前瞻检测
  └─ compress() Phase 2.5 — 存档集成点

run_agent/_agent_monolith.py
  └─ ContextCompressor 初始化传入 session_db + compress() 传入 session_id

hermes_cli/commands.py + gateway/run.py
  └─ /uncompress 命令 — 路由 + handler
```

## Step 1: Schema 准备

### 1.1 升级 SCHEMA_VERSION

在 `hermes_state.py` 中：
```python
SCHEMA_VERSION = 7  # 旧版 +1
```

### 1.2 添加新表到 SCHEMA_SQL

```sql
CREATE TABLE IF NOT EXISTS compressed_archives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    compression_round INTEGER NOT NULL,
    archived_at REAL NOT NULL,
    summary_text TEXT,
    knowledge_fingerprint TEXT,
    n_messages INTEGER,
    n_tokens_saved INTEGER,
    messages_json TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_compressed_archives_session
    ON compressed_archives(session_id, compression_round);
```

### 1.3 添加版本迁移

```python
if current_version < 7:
    cursor.execute("UPDATE schema_version SET version = 7")
```

### 1.4 添加 SessionDB 方法

五个方法：`save_compressed_archive`, `get_compressed_archives`, `get_compressed_archive_count`, `delete_compressed_archives`

## Step 2: ContextCompressor 改造

### 2.1 添加 session_db 参数到 `__init__`

```python
def __init__(self, ..., session_db: Any = None):
    self.session_db = session_db
```

### 2.2 添加前瞻检测

在 should_compress() 中加入 `_token_history` 追踪：连续 3 轮增长 >10% 时提前触发 fast_trim。

### 2.3 添加 _extract_knowledge_fingerprint()

正则提取：
- 文件路径: `(?:/[\w.\-]+)+`
- 命令: `(?:`[^`]{10,}`|```bash\n...)`
- 键值: `api_key|token|secret|endpoint` 等模式
- 工具名: 从 tool_calls 中提取

### 2.4 在 compress() 中插入 Phase 2.5

在计算完 `turns_to_summarize` 后、LLM 摘要之前：

```python
if self.session_db and session_id:
    archive_msgs_json = json.dumps([...])
    fingerprint = _extract_knowledge_fingerprint(turns_to_summarize)
    self.session_db.save_compressed_archive(
        session_id=session_id,
        compression_round=self.compression_count + 1,
        messages_json=archive_msgs_json,
        ...
    )
```

## Step 3: 调用链集成

### 3.1 _agent_monolith.py 中传递 session_db

```python
self.context_compressor = ContextCompressor(
    ...,
    session_db=getattr(self, "_session_db", None),
)
```

### 3.2 确保 compress() 传入 session_id

```python
compressed = self.context_compressor.compress(
    messages, current_tokens=approx_tokens,
    session_id=self.session_id or "",
)
```

## Step 4: /uncompress 命令

### 4.1 注册命令

`hermes_cli/commands.py`:
```python
CommandDef("uncompress", "Show conversation content from past compression archives", "Session",
           aliases=("archives",), args_hint="[N]"),
```

### 4.2 Gateway handler

`gateway/run.py`:
- `_handle_uncompress_command`: 用 `self._session_db.get_compressed_archives()` 取数据
- 展示格式：压缩轮次、摘要预览、知识指纹（文件/命令/键值/工具）、首尾消息样例

## 已知 Pitfalls

### ⚠️ compress() 不调用 should_compress()

compress() 内部用自己的 `_get_compression_level(display_tokens)` 判断是否压缩。如果 `display_tokens < self.threshold_tokens`，直接返回原始 messages，**不经过压缩逻辑**。这意味着：

- 测试必须设置 `last_prompt_tokens >= threshold_tokens` 或传入 `current_tokens >= threshold_tokens`
- 前瞻检测在 `should_compress()` 层有效，不干扰 compress() 内部逻辑

### ⚠️ 测试修复

工作区已有的 `context_compressor.py` 修改在压缩逻辑中增加了 `_get_compression_level` 检查，但测试没有设置足够高的 `last_prompt_tokens`。需要：

```python
# 在每个调用 compress() 的测试方法中添加:
c.last_prompt_tokens = 90000  # 超过 threshold_tokens
# 或:
c.compress(messages, current_tokens=110_000)  # 超过 threshold_tokens
```

### ⚠️ session_id 追踪

- SQLite sessions 表可能有很多个，gateway 管理 session_store 在**内存中**
- 要确保存档写入的 session_id 就是 gateway 当前用的那个
- 如果遇到"没有存档"的问题，检查 session_id 是否匹配

### ⚠️ compressed_archives 与 prune_sessions 联动

prune_sessions 必须同步删除 archived 数据，否则会留下孤行：

```python
conn.execute("DELETE FROM compressed_archives WHERE session_id = ?", (sid,))
```
