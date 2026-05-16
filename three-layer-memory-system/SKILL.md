---
name: three-layer-memory-system
description: "为 Hermes Agent 添加三层记忆子系统（情景记忆Episodic + 语义记忆Semantic + 程序性记忆Procedural）的标准化流程。涵盖 schema 扩展、SQLite CRUD 封装、工具注册、AIAgent 生命周期 hook。"
category: software-development
---

# Three-Layer Memory System for Hermes Agent

## When to Use

当需要为 Hermes Agent 添加新的持久化记忆/数据子系统时。具体场景：
- 需要新的结构化数据表（不是简单文件存储）
- 数据需要跨 session 持久化和检索
- 需要将数据暴露为 LLM 可调用的工具
- 需要在 agent 生命周期自动触发读写

## Architecture

```
hermes_state.py           → schema 定义 + 迁移（SCHEMA_VERSION bump）
hermes_state_<name>.py    → SQLite CRUD 封装层
tools/<name>_tool.py      → 自注册工具（registry.register）
toolsets.py               → 工具注入 _HERMES_CORE_TOOLS
model_tools.py            → 导入链注册
run_agent/_agent_monolith.py → AIAgent 生命周期 hook
```

## Step-by-Step

### Step 1: Schema 扩展

在 `hermes_state.py` 中：

1. **bump SCHEMA_VERSION**（当前最大版本 +1）
2. **在 SCHEMA_SQL 末尾**添加 CREATE TABLE 语句
3. **在 migration 块末尾**添加版本升级逻辑

```python
SCHEMA_VERSION = 9  # 当前最大 +1

# 在 SCHEMA_SQL 的 commits_index 之后添加：
CREATE TABLE IF NOT EXISTS my_new_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ...
);

# 在 migration if block 末尾添加：
if current_version < 9:
    # v9: description of what changed
    cursor.execute("UPDATE schema_version SET version = 9")
```

**关键原则**：CREATE TABLE 写进 SCHEMA_SQL（新建安装自动建表），migration 块只 bump 版本号（已有数据库通过 SCHEMA_SQL 的 IF NOT EXISTS 安全创建）。

### Step 2: SQLite CRUD 封装

创建 `hermes_state_<name>.py`：

```python
from pathlib import Path
from hermes_constants import get_hermes_home

class MyStore:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or get_hermes_home() / "state.db"
    
    def _get_conn(self):
        """Read-only connection for queries."""
        import sqlite3
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _execute(self, sql: str, params: tuple = None) -> Any:
        """Write with BEGIN IMMEDIATE + jitter retry (same pattern as SessionDB)."""
        import sqlite3, random, time
        last_err = None
        for attempt in range(10):
            try:
                conn = sqlite3.connect(str(self.db_path), timeout=1.0)
                conn.row_factory = sqlite3.Row
                conn.execute("BEGIN IMMEDIATE")
                try:
                    cur = conn.cursor()
                    cur.execute(sql, params or ())
                    conn.commit()
                    return cur.lastrowid
                except BaseException:
                    conn.rollback()
                    raise
                finally:
                    conn.close()
            except sqlite3.OperationalError as exc:
                if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                    last_err = exc
                    time.sleep(random.uniform(0.02, 0.15))
                    continue
                raise
        raise last_err or RuntimeError("Write failed after retries")
```

**注意**：复用 SessionDB 的 WAL + jitter retry 模式，不要自己另造连接管理。使用 `state.db` 同一数据库保持事务一致性。

### Step 3: 工具注册

创建 `tools/<name>_tool.py`：

```python
import json, logging
from tools.registry import registry

_global_store = None

def set_store(store):
    global _global_store
    _global_store = store

def get_store():
    global _global_store
    if _global_store is None:
        from hermes_state_xxx import MyStore
        _global_store = MyStore()
    return _global_store

def my_search_tool(query: str = "", limit: int = 10, **kw) -> str:
    try:
        store = get_store()
        results = store.search(query=query, limit=min(limit, 20))
        return json.dumps({"success": True, "count": len(results), "results": results}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def check_reqs() -> bool:
    return True

registry.register(
    name="my_search",
    toolset="memory",  # 放入 memory toolset 以便和现有记忆系统一起管理
    schema={
        "name": "my_search",
        "description": "...",
        "parameters": {
            "type": "object",
            "properties": {...},
            "required": [],
        },
    },
    handler=lambda args, **kw: my_search_tool(query=args.get("query", ""), ...),
    check_fn=check_reqs,
)
```

**坑**：handler 必须返回 JSON string（不是 dict）。

### Step 4: 工具注入

**toolsets.py** — 在 `_HERMES_CORE_TOOLS` 中添加工具名：
```python
"my_search", "my_store",
```

**model_tools.py** — 在 `_discover_tools()` 的 `_modules` 列表中添加：
```python
"tools.my_tool",
```

### Step 5: AIAgent 生命周期 hook

在 `run_agent/_agent_monolith.py` 中：

1. **init 阶段注入 store**（在 `self._memory_store` 初始化之后）：
```python
self._my_store = None
try:
    from hermes_state_xxx import MyStore
    from tools.my_tool import set_store
    self._my_store = MyStore()
    set_store(self._my_store)
except Exception:
    pass
```

2. **close() 阶段自动触发**（在 step 5 后加 step 6）：
```python
# 6. Save X data (best-effort)
try:
    self._save_my_data()
except Exception:
    pass
```

3. **添加对应方法**：
```python
def _save_my_data(self):
    store = getattr(self, "_my_store", None)
    if not store:
        return
    # collect data from self._session_messages or other state
    store.store(...)
```

## Pitfalls

1. **DO NOT hardcode db_path** — 使用 `get_hermes_home() / "state.db"`，否则多 profile 下数据隔离会失效
2. **DO NOT use sqlite3.Row outside with-block** — Row 对象在 connection close 后不可用；在 fetchall() 后立即转换为 dict
3. **JSON 字段** — 存储 List/Dict 字段时用 `json.dumps()` 序列化，读取时用 `json.loads()`。注意 None 和空字符串的处理
4. **导入链** — `hermes_state_xxx.py` 中不要引用 `tools/` 或 `run_agent/`，避免循环导入。工具模块中引用 store 类时会触发延迟导入
5. **retry pattern** — 不要用 sqlite3 内置 timeout（30s 太长），用 1s timeout + 应用层 jitter retry（20-150ms 随机）
6. **Schema 版本** — 每次新加表/列必须 bump SCHEMA_VERSION。migration 块中的 ALTER TABLE 必须有 try/except（列可能已存在）
7. **工具在 session 启动后才可见** — 新注册的工具在当前运行的 session 中不可用；需要新 session（新 chat）才能使用
8. **Schema 字段一致性** — 如果存在两个 schema 定义源（hermes_state.py 的 SCHEMA_SQL 和 hermes_state_xxx.py 的内联 schema），字段名和类型必须完全一致。不一致会导致运行时 SQL 错误。**推荐的做法**：用一个源定义 schema，另一个引用它
9. **store_semantic 方法的入参类型** — 不要用 dataclass 对象作为 `store_semantic()` 的入参，用位置参数 `(category, fact, confidence, source_session_id, source)`。dataclass 字段名变化会导致调用侧静默失败
10. **LLM 自动提取的 token 控制** — 对话事实提取（语义记忆自动填充）时限制：最多最后 5 条用户消息，每条截断 300 字符。一次提取调用约 2K token 即可完成
11. **一次性 backfill 标记** — 批量回溯旧数据时用标记文件 (`get_hermes_home() / ".xxx_backfill_done"`) 确保只执行一次。不要依赖数据库自身去重来限制执行次数
12. **两个 store 并存模式** — `MemoryStoreV2` 可能和 `SessionDB` 都写同一个 `state.db`。确保 `MemoryStoreV2` 有自己的 schema 初始化（`CREATE TABLE IF NOT EXISTS`），不要依赖 SessionDB 的 migration 来建表。两者是完全独立的类

15. **Schema 字段不匹配的排查路径** — 当出现类似 `OperationalError: no such column: source_session` 的错误时，**四个地方必须一致**：hermes_state.py 的 SCHEMA_SQL 中的列名、hermes_state_xxx.py 内联 schema 中的列名、dataclass 的字段名、store_semantic SQL INSERT/SELECT 中引用的列名。不一致时执行以下排查：
    - 先看 `MemoryStoreV2` 的 `_SEMANTIC_SCHEMA` 建表 SQL 用的是什么列名
    - 再看 `search_semantic` SELECT 语句用的是什么列名
    - 再看 `store_semantic` 方法签名参数名
    - 最后看测试中创建表时用的是什么列名（如果测试自己建了表而不是复用 MemoryStoreV2 的 schema）
    - 修复顺序：先改 dataclass 字段名 → 改内联 schema SQL → 改所有 INSERT/SELECT 引用 → 改方法签名 → 改所有调用点
    - 注意：如果两个独立的 schema 初始化代码（SessionDB 的 SCHEMA_SQL 和 MemoryStoreV2 的 _SEMANTIC_SCHEMA）都创建同一张表但列名不同，实际生效的是**先执行的那个**。确认哪个先初始化，统一用它的列名
13. **语义记忆自动提取 hook** — 在 `_save_episodic_memory()` 尾部调用 `_extract_semantic_facts(messages)`。用辅助 LLM（auxiliary_client.call_llm）提取事实，返回 JSON 数组。所有提取结果用 `store.store_semantic(category="fact", fact=..., confidence=0.6, source_session_id=..., source="auto-extract")` 存入。注意只传最后 5 条用户消息给 LLM 以控制 token
14. **旧 session backfill** — 在 AIAgent init 尾部触发 `_backfill_legacy_sessions()`，调用 `MemoryStoreV2.backfill_episodic_from_sessions(max_sessions=100)`。扫描 state.db 的 sessions 表，找有消息记录但不在 episodic_memory 中的 session。用标记文件 `.episodic_backfill_done` 控制只执行一次。backfill 的条目 tags 标记为 `["backfill"]`

## Verification

```bash
# 1. 语法检查
python3 -c "import py_compile; py_compile.compile('hermes_state_xxx.py', doraise=True); print('OK')"

# 2. 导入测试
python3 -c "import importlib; importlib.import_module('tools.xxx_tool'); from tools.registry import registry; print([e.name for e in registry._tools.values()])"

# 3. 端到端测试（临时 HERMES_HOME）
python3 -c "
import tempfile, os; os.environ['HERMES_HOME'] = tempfile.mkdtemp()
from hermes_state import SessionDB
from hermes_state_xxx import MyStore
# CRUD operations...
"

# 4. 回归测试
python3 -m pytest tests/test_toolsets.py -q
python3 -m pytest tests/tools/test_memory_tool.py -q
```
