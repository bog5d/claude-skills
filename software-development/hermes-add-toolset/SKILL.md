---
name: hermes-add-toolset
description: 为Hermes Agent新增工具模块的标准化流程。从创建tools/xxx.py到注册到model_tools.py和toolsets.py再到写测试的完整SOP。
---

# Hermes 新增工具模块 SOP

## 触发条件
需要为Hermes Agent新增一个工具模块（如浏览器操控、新API集成、训练工具等）。

## 工作流

### 第1步：创建 tools/your_tool.py

```python
#!/usr/bin/env python3
"""工具模块描述"""
import json
import logging
from tools.registry import registry

logger = logging.getLogger(__name__)

def check_requirements() -> bool:
    return True  # 或检查API key等

def your_tool_handler(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True})

registry.register(
    name="your_tool_name",
    toolset="your-toolset",
    schema={
        "name": "your_tool_name",
        "description": "工具描述",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "参数描述"},
            },
            "required": ["param"],
        },
    },
    handler=lambda args, **kw: your_tool_handler(
        param=args.get("param", ""),
        task_id=kw.get("task_id"),
    ),
    check_fn=check_requirements,
    requires_env=[],
)
```

### 第2步：注册到 model_tools.py

在 `_discover_tools()` 函数的 `_modules` 列表末尾添加：

```python
"tools.your_tool",  # 工具描述
```

### 第3步：注册到 toolsets.py

**3a.** 在 `_HERMES_CORE_TOOLS` 列表末尾添加工具名：
```python
"your_tool_name",
```

**3b.** 在 `TOOLSETS` 字典中添加toolset定义（放在适当位置）：
```python
"your-toolset": {
    "description": "工具集描述",
    "tools": ["your_tool_name"],
    "includes": [],
    "requires_env": ["REQUIRED_ENV_VAR (how to get it)"],
},
```

### 第4步：验证导入

```bash
cd /Users/mac/.hermes/hermes-agent && source venv/bin/activate
python3 -c "import tools.your_tool; from tools.registry import registry; print(registry.get_toolset_for_tool('your_tool_name'))"
```

应输出 `your-toolset`。

### 第5步：写测试

创建 `tests/test_your_tool.py`：

```python
import json
import pytest
from tools.your_tool import your_tool_handler

def test_basic():
    result = your_tool_handler(param="test")
    data = json.loads(result)
    assert data["success"] is True
```

运行：`python -m pytest tests/test_your_tool.py -v`

### 第6步：跑全量回归

```bash
python -m pytest tests/ -q --tb=short
```

## 关键模式

### 工具handler签名
```python
def handler(args, **kw) -> str:
    # args = 模型传入的参数字典
    # kw 包含 task_id 等上下文
    # 必须返回JSON字符串
```

### registry.register() 参数
- `name`: 工具名（snake_case，全局唯一）
- `toolset`: toolset名（kebab-case）
- `schema`: OpenAI function calling格式
- `handler`: 调用处理函数
- `check_fn`: 返回bool，检查工具是否可用
- `requires_env`: 需要的环境变量列表

### 不需要改动的文件
- `run_agent.py` — 自动发现
- `cli.py` — 通过registry自动获取

## 踩坑

1. **schema.description必须准确** — 模型根据描述决定是否调用工具，描述不准确会导致工具不被使用
2. **handler必须返回JSON字符串** — 返回dict会被registry包装层报错
3. **toolset名用kebab-case** — `mcp-server` 不是 `mcp_server`
4. **测试时显式关闭其他filter** — 如测 `require_tool_calls` 时设 `require_completed=False`，否则默认值会干扰
