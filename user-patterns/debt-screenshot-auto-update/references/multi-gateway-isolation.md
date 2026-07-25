# 多 Gateway Profile 隔离守卫

## 背景（2026-07-25 踩坑）

波总运行 4 个 Hermes gateway：
- `ai.hermes.gateway`（default）
- `ai.hermes.gateway-her-m2`
- `ai.hermes.gateway-finance`（首席财务官）
- `ai.hermes.gateway-english-tutor`

`finance_ocr` 工具原注册在 `_HERMES_CORE_TOOLS`（toolsets.py 第41行），所有 profile 都能看到和调用。
三个主力 gateway 都可能收到波总的截图 → 调用 `finance_ocr` → 修改 `debts.json`。
波总分不清哪个 AI 在回他，数据被反复覆盖。

## 两层隔离架构

### Layer 1：check_fn（工具不可见）

```python
def check_finance_ocr_requirements() -> bool:
    """OCR tool requires ocr_finance.py script AND finance profile."""
    if not OCR_SCRIPT.is_file():
        return False
    hermes_home = os.environ.get("HERMES_HOME", "")
    if "finance" not in hermes_home:
        return False
    return True
```

**效果：** 非 finance profile 的 AI 在 schema 中就看不到 `finance_ocr` 工具，无法调用。
**文件：** `/Users/mac/.hermes/hermes-agent/tools/finance_ocr_tool.py`

### Layer 2：_ocr() 运行时守卫（不可写）

```python
if not is_finance_profile and not dry_run:
    return json.dumps({
        "success": False,
        "error": "⛔ 非 finance profile 禁止修改财务数据。请通过 finance gateway 操作。",
    })
```

**效果：** 即使绕过 check_fn（如直接调底层 Python），写操作也被拒绝。
`--dry-run` 预览模式下允许通过（不写数据）。

## 关键依赖

- 隔离机制依赖 `HERMES_HOME` 环境变量正确设置
- finance gateway 的 `HERMES_HOME` = `/Users/mac/.hermes/profiles/finance`
- 其他 gateway 的 `HERMES_HOME` = 各自 profile 路径（不含 "finance"）
- 所有 gateway 的 launchd plist 必须显式传递 `HERMES_HOME`

## 验证命令

```bash
# 检查 check_fn 行为
ps aux | grep hermes | grep gateway
# 每个 gateway 的 HERMES_HOME 应该指向各自 profile

# 模拟非 finance profile 调用（应被拒绝）
HERMES_HOME=/Users/mac/.hermes/profiles/her-m2 python3 -c "
from tools.finance_ocr_tool import check_finance_ocr_requirements
print(f'check_fn returns: {check_finance_ocr_requirements()}')
# 应输出 False
"
```

## 注意事项

- `check_fn` 在工具发现（discovery）阶段执行，不是每次调用都执行
- 如果 gateway 已启动，修改 `check_fn` 后需要重启 gateway 才能生效
- `finance` toolset 在 `toolsets.py` 中定义（第556-560行），但 `finance_ocr` 仍保留在 `_HERMES_CORE_TOOLS` 中（第40-41行），以保持 schema 一致性——隔离由 `check_fn` 实现，不是靠移除工具集
