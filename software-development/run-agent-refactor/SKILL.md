---
name: run-agent-refactor
description: 拆分 run_agent.py（9700 行单文件）为 run_agent/ 包结构，包含 AIAgentContext、ConversationLoop、ToolExecutor 等模块
trigger: hermes codebase refactoring
---

# run_agent.py 重构：包拆分计划

## 目标
将 `/Users/mac/.hermes/hermes-agent/run_agent.py`（~9800 行）拆分为 `run_agent/` 包：

```
run_agent/
  __init__.py           # AIAgent 门面类，保持向后兼容
  agent_context.py      # AIAgentContext dataclass — 替代 57 参数 __init__
  conversation_loop.py  # 主循环状态机（PREPARE → API_CALL → TOOL_EXEC → RESULT）
  tool_executor.py      # 工具调度 + 并行执行
  session_manager.py    # 会话生命周期
  llm_client.py         # API 调用封装
  callbacks.py          # 所有回调聚合（tool_progress, thinking, ...）
```

## 原则
1. **不改外部接口** — `from run_agent import AIAgent` 继续工作
2. **不删代码** — 只移动和组织，不重写逻辑
3. **测试全覆盖** — 拆完后所有现有测试通过

## 关键原则（从实战中得出）

1. **不要立即移动代码** — 先把原文件重命名为 `_agent_monolith.py`，创建 `__init__.py` 做导入转发。所有测试期望从 `run_agent` 导入的符号都要在 `__init__.py` 中重新导出
2. **保留原文件直到所有测试通过** — `_agent_monolith.py` 保持完整 AIAgent 实现，后续逐步提取模块
3. **模块级常量和正则** — 如 `_SURROGATE_RE` 是模块级变量，必须在 `__init__.py` 的 `from ._agent_monolith import` 中显式列出
4. **Monkeypatch 兼容** — 测试文件（如 `test_dict_tool_call_args.py`）会 `from run_agent import OpenAI, get_tool_definitions, handle_function_call` 做 monkeypatch。这些必须在 `__init__.py` 中重新导出（`from openai import OpenAI as OpenAI` + `from model_tools import ...`）

## 实际步骤

### Step 1: 创建 `run_agent/` 目录 + 移动原文件
```bash
mkdir run_agent/
mv run_agent.py run_agent/_agent_monolith.py
```

### Step 2: 创建 `run_agent/__init__.py`（门面类）
- 从 `_agent_monolith` 重新导出所有测试和外部代码引用的符号
- 必须导出：`AIAgent`, `IterationBudget`, `_SafeWriter`, `_SURROGATE_RE`, `_sanitize_surrogates`, `_sanitize_messages_surrogates`, `_strip_non_ascii`, `_strip_budget_warnings_from_history`, `_qwen_portal_headers`, `main`
- 额外导出 monkeypatch 目标：`from openai import OpenAI as OpenAI`, `from model_tools import get_tool_definitions, handle_function_call`

### Step 3: 创建 `run_agent/agent_context.py`
- 从 `AIAgent.__init__` 提取参数为 `AIAgentContext` dataclass（但注意：先不做实际提取，先确保所有导入正常）
- 标记哪些是必填的、哪些有默认值

### Step 4: 创建 `run_agent/callbacks.py`
- 回调类型定义：`OnToolStart = Callable[[str, dict], None]`, `OnToolEnd = Callable[[str, str], None]` 等
- noop 默认回调

### Step 5: 逐步提取模块（后续迭代）
- conversation_loop.py
- tool_executor.py
- session_manager.py
- llm_client.py

## 验证
```bash
source venv/bin/activate
cd /Users/mac/.hermes/hermes-agent

# 1. 确保 AIAgent 导入继续工作
python3 -c "from run_agent import AIAgent; a = AIAgent(model='test', skip_memory=True); print('OK:', type(a).__name__)"

# 2. 跑全量测试（跳过已知不稳定的）
python -m pytest tests/ -q --no-header 2>&1 | tail -10
```

## 已知的不稳定测试（与重构无关）
- `tests/gateway/test_email.py::TestChannelDirectory::test_email_in_session_discovery`
- `tests/gateway/test_telegram_conflict.py::test_polling_conflict_retries_before_fatal`
- `tests/gateway/test_run_progress_topics.py::test_run_agent_progress_stays_in_originating_topic`
- `tests/gateway/test_approve_deny_commands.py::TestBlockingApprovalE2E::test_blocking_approval_approve_once`
- `tests/cron/test_codex_execution_paths.py::test_cron_run_job_codex_path_handles_internal_401_refresh`

这些失败的根因是 emoji 变更、网络超时、异步竞争条件，不是重构引入。

## 验证
```bash
source venv/bin/activate
cd /Users/mac/.hermes/hermes-agent

# 1. 确保 AIAgent 导入继续工作
python3 -c "from run_agent import AIAgent; print('OK:', AIAgent)"

# 2. 运行现有测试
python -m pytest tests/ -q --no-header 2>&1 | tail -5
```

## 风险
- `run_agent.py` 中有大量模块级 import（约 80+ 行），拆包时可能导致循环导入
- `self._xxx` 属性在多个方法间共享，需要在 context 中正确映射
- `AIAgent.__init__` 有复杂的条件逻辑（根据 platform 配置不同的 toolsets），重构时要保留所有条件分支不变