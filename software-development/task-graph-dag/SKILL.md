---
name: task-graph-dag
description: 实现 DAG 任务图系统，支持多步并行任务编排。新增 tools/task_graph.py，在 delegate_tool 中注册 plan_task 和 task_graph 工具。
trigger: need structured task orchestration
---

# TaskGraph DAG 任务图实现

## 目标
在 Hermes Agent 中实现 DAG 任务编排系统，让 agent 可以：
1. 预先制定多步执行计划（plan_task）
2. 按 DAG 执行，自动并行无依赖步骤（task_graph）
## 实现总结（基于实战）

**文件：** `/Users/mac/.hermes/hermes-agent/tools/task_graph.py`（651 行，已创建并通过验证）

## 核心数据结构

```python
@dataclass
class TaskStep:
    name: str
    depends_on: List[str]     # 依赖的步骤名
    toolsets: List[str]       # 子步骤可用的工具集
    prompt: str               # 子步骤指令
    max_iterations: int = 30
    timeout: int = 300
    retry_count: int = 0
    output_key: str = ""      # 输出标识，供下游引用

@dataclass
class TaskPlan:
    plan_id: str
    goal: str
    steps: List[TaskStep]
    max_concurrency: int = 3
    on_step_failure: str = "abort"  # abort | continue | skip_dependents
    status: str = "pending"         # pending | running | completed | failed
```

## 注册方式
```python
# 直接在 task_graph.py 末尾的 _register_tools() 中：
registry.register(name="plan_task", toolset="task_graph", ...)
registry.register(name="task_graph", toolset="task_graph", ...)

# toolsets.py 中手动追加：
_HERMES_CORE_TOOLS += ["plan_task", "task_graph"]
```

## 工具 API

### `plan_task(goal, steps_json, max_concurrency=3, on_step_failure="abort")`
- steps_json: JSON 字符串数组，每个元素是 TaskStep 的 dict 表示
- 使用 Kahn 算法做拓扑排序
- 检测循环依赖（A→B→C→A 会被拒绝，返回 `{"error": "...", "valid": false}`）
- 返回执行批次列表（batch 0 = 无依赖的步骤并行执行，batch 1 = 依赖 batch 0 的步骤，etc.）
- plan_id 是基于 uuid4 的短 ID（如 "fb6bbae5-63f"）

### `task_graph(plan_id, agent_factory=None)`
- 按 DAG 执行：批次内并行（ThreadPoolExecutor），批次间串行
- 超时控制：每个步骤有独立的 timeout
- 重试：retry_count > 0 时失败自动重试

## 数据传递
- 中间结果存储到 `~/.hermes/task_graph/<plan_id>/<step_name>.json`
- 下游步骤可以用 `{{ steps.step_name.output }}` 语法在 prompt 中引用上游结果
- 由 `_resolve_prompt_template()` 函数解析

## 验证
```python
source venv/bin/activate && python3 << 'PYEOF'
import json, sys
sys.path.insert(0, '/Users/mac/.hermes/hermes-agent')
import tools.task_graph

# 正常 DAG
result = tools.task_graph.plan_task(
    goal="Test", steps_json=json.dumps([
        {"name": "A", "depends_on": [], "toolsets": [], "prompt": "A"},
        {"name": "B", "depends_on": [], "toolsets": [], "prompt": "B"},
        {"name": "C", "depends_on": ["A", "B"], "toolsets": [], "prompt": "C"},
    ]))
# 预期: batches=[[A,B],[C]]

# 循环检测
result = tools.task_graph.plan_task(
    goal="Cycle", steps_json=json.dumps([
        {"name": "A", "depends_on": ["C"], ...},
        {"name": "B", "depends_on": ["A"], ...},
        {"name": "C", "depends_on": ["B"], ...},
    ]))
# 预期: {"error": "Cycle detected...", "valid": false}
PYEOF
```

## 验证
```bash
source venv/bin/activate
cd /Users/mac/.hermes/hermes-agent

# 测试注册
python3 -c "import tools.task_graph; from tools.registry import registry; print('plan_task:', 'plan_task' in registry._tools); print('task_graph:', 'task_graph' in registry._tools)"

# 运行测试
python -m pytest tests/ -q --no-header 2>&1 | tail -5
```

## 注意事项
- 不要破坏现有的 delegate_task 功能
- DAG 拓扑排序要检测环（cycle detection）
- 并行度可配置，默认 3
- 步骤失败策略要支持：中止/继续/重试
- 跨步骤数据传递用临时文件（`~/.hermes/task_graph/<plan_id>/<step_name>.json`）