---
name: self-improvement-mechanism
description: "为 Hermes Agent 添加自改进机制——对话完成后自动反思、提取成功/失败模式、生成错误指纹、存储经验事实到语义记忆、检测技能候选。涵盖反思引擎设计、run_conversation() hook、语义记忆写入、marker 驱动的批处理回溯。"
category: software-development
---

# Self-Improvement Mechanism for Hermes Agent

## When to Use

当需要让 Hermes Agent 从已完成对话中学习时：
- 对话完成后自动分析工具调用序列
- 提取成功模式和失败模式
- 生成可重用的错误指纹（未来快速匹配已知错误）
- 将经验自动存入语义记忆
- 检测可抽取为 skill 的工作流模式

## Architecture

```
hermes_self_improve.py        → 反思引擎（分析、提取、生成）
tools/self_reflect_tool.py    → 手动触发反思的工具
run_agent/_agent_monolith.py  → run_conversation() exit hook
  └─ _generate_task_reflection()
hermes_state_memory.py        → save_reflection_to_memory() 写入 semantic_memory
```

## Step-by-Step

### Step 1: 反思引擎

创建 `hermes_self_improve.py`，核心函数：

```python
def should_reflect(messages, api_call_count) -> bool:
    """判断是否值得反思。条件：>=3 次工具调用且有实际工具序列"""
    
def generate_reflection(messages, api_call_count, model, session_id, platform) -> dict:
    """生成结构化反思。返回：
      - task_summary, tool_sequence, errors, outcome, 
        patterns, experience_facts, suggested_skill
    """
    
def save_reflection_to_memory(reflection, memory_store) -> int:
    """将经验事实写入 semantic_memory"""
```

**分析流程：**
1. `_extract_tool_sequence()` — 从 messages 中提取有序的工具调用 + 结果配对
2. `_extract_errors()` — 从 tool result 中提取错误信息 + 计算错误指纹
3. `_determine_outcome()` — 判断 session 是否成功
4. `_extract_patterns()` — 检测工具成功率、重试模式、委托模式
5. `_generate_experience_facts()` — 将模式转化为可存储的经验
6. `_generate_skill_suggestion()` — 成功且 >=8 次调用的会话生成技能候选

### Step 2: 注册 self_reflect 工具

```python
# tools/self_reflect_tool.py
registry.register(
    name="self_reflect",
    toolset="memory",
    schema={"name": "self_reflect", ...},
    handler=...,
    check_fn=lambda: True,
)
```

### Step 3: AIAgent hook

在 `run_agent/_agent_monolith.py` 中：

**run_conversation() 尾部**（在 `_save_trajectory()` 之后、`_cleanup_task_resources()` 之前）：

```python
# Week 5: Self-Improvement — auto-reflect on completed sessions
self._generate_task_reflection(
    messages=messages,
    api_call_count=api_call_count,
    iteration_limit_hit=(final_response is None or api_call_count >= self.max_iterations),
)
```

**_generate_task_reflection 方法：**

```python
def _generate_task_reflection(self, messages, api_call_count, iteration_limit_hit=False):
    from hermes_self_improve import should_reflect, generate_reflection, save_reflection_to_memory
    
    if not should_reflect(messages, api_call_count):
        return
    
    reflection = generate_reflection(messages=messages, api_call_count=api_call_count, ...)
    
    # Store to semantic memory
    store = getattr(self, "_tri_memory_store", None)
    if store:
        stored = save_reflection_to_memory(reflection, store)
    
    # Check for skill suggestion
    skill = reflection.get("suggested_skill")
    if skill and skill.get("confidence", 0) >= 0.7:
        self._pending_skill_suggestion = skill
```

## Key Constants

```python
_MIN_TOOL_CALLS_FOR_REFLECTION = 3   # 最少工具调用数才触发反思
_MIN_TOOL_CALLS_FOR_SKILL = 8        # 最少工具调用数才考虑技能
_CATEGORY_SUCCESS = "experience-success"
_CATEGORY_FAILURE = "experience-failure"
_CATEGORY_PATTERN = "experience-pattern"
_CATEGORY_NOTE = "experience-note"
```

## Error Fingerprinting

```python
def _compute_error_fingerprint(error_text: str) -> str:
    \"\"\"标准化错误指纹。去掉路径、行号、hex地址、大数字。
    
    Input:  "Error: /Users/mac/project/file.py line 42: Permission denied (0x7fff)"
    Output: "Error: PATH line N: Permission denied (0xHEX)"
    
    用于去重和未来快速匹配已知错误。
    \"\"\"
```

## Pitfalls

1. **不应在简单问答上浪费 token** — should_reflect() 必须过滤掉 <=2 次工具调用的短会话
2. **技能候选不应自动创建** — 只记录到 log 和 `_pending_skill_suggestion`，等待用户确认后再调用 `skill_manage(create)`
3. **store_semantic 用位置参数** — 调用 `save_reflection_to_memory` 时传入的是 `(category, fact, confidence, source_session_id, source)`，不是 dataclass 对象。字段名必须和 `hermes_state_memory.py` 中的 `store_semantic()` 方法签名一致
4. **经验事实去重** — `store_semantic()` 用 `fact = ? AND category = ?` 精确匹配去重。重复存储同一 reflection 得到 0 个新记录
5. **不要在反思引擎中引入 LLM 调用** — 目前的实现是纯 Python 模式匹配，没有额外的 API 调用。这是故意的——保持低成本
6. **会话元数据缺失** — `generate_reflection` 依赖消息结构中的 `tool_calls`、`function.name`、`function.arguments` 等字段。如果消息结构不标准需加兜底处理
7. **`_pending_skill_suggestion` 是临时属性** — 只在当前 agent 实例生命周期内有效，不会跨 session 持久化

## 与三层记忆系统的关系

```
Week 4 (三层记忆)                    Week 5 (自改进)
┌──────────────┐                   ┌────────────────┐
│ episodic_mem │                   │ self_reflect    │
│ semantic_mem │ ◄── 写入 ─────── │ (反思引擎)      │
│   (经验存储)  │                   │                │
└──────────────┘                   └────────────────┘
       ▲                                   │
       │                                   ▼
  backfill()                        对话完成自动触发
  (旧session回溯)                    (run_conversation hook)
```

## Verification

```bash
# 1. 语法检查
python3 -c "import py_compile; py_compile.compile('hermes_self_improve.py', doraise=True); print('OK')"

# 2. 导入测试
python3 -c "
from hermes_self_improve import should_reflect, generate_reflection, save_reflection_to_memory
from hermes_self_improve import _extract_tool_sequence, _compute_error_fingerprint
"

# 3. 工具注册
python3 -c "
import importlib; importlib.import_module('tools.self_reflect_tool')
from tools.registry import registry
assert 'self_reflect' in [e.name for e in registry._tools.values()]
"

# 4. 模拟会话测试
python3 -c "
import tempfile, os; os.environ['HERMES_HOME'] = tempfile.mkdtemp()
from hermes_state_memory import MemoryStoreV2
from hermes_self_import import generate_reflection, save_reflection_to_memory

messages = [大量工具调用的测试数据]
reflection = generate_reflection(messages, api_call_count=8)
stored = save_reflection_to_memory(reflection, MemoryStoreV2())
"
```

## 测试故障排查

| 症状 | 根因 | 修复 |
|------|------|------|
| 反思从不触发 | `_MIN_TOOL_CALLS_FOR_REFLECTION=3` 但 `api_call_count` 传递为 0 | 检查 hook 调用处的参数传递 |
| 技能建议总为 None | 工具调用数 <8 或 reflection 的 `successful` 为 False | 降低阈值或检查 `_determine_outcome()` |
| 去重失败 | `store_semantic` 的 `fact` 和 `category` 组合不唯一 | 检查两次调用是否传递了完全相同的参数 |
| semantic_memory 表字段不匹配 | two schema definitions 冲突 | 统一用 `source_session_id` / `source` 字段名 |
