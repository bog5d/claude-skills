---
name: officecli-agent-native-office
description: 用 OfficeCLI (iOfficeAI) 创建/编辑/渲染 Word、Excel、PPT —— Agent 原生无 Office 应用依赖。覆盖安装、MCP 注册、跨 Agent 集成和文档生成流水线。
---

# OfficeCLI — Agent 原生 Office 文档自动化

## 是什么

[OfficeCLI](https://github.com/iOfficeAI/OfficeCLI) — 一个使 Agent 无需 Microsoft Office 即可创建、编辑和渲染 Word/Excel/PPT 文档的 CLI 工具（Apache 2.0, 15.7k+ stars）。内置 HTML 渲染引擎，支持将文档预览为 PNG 截图供 Agent 视觉审校。支持 350+ Excel 公式，公式求值在 CLI 内部完成，无需外部应用打开即可验证结果。

## 安装

**优先使用官方脚本，而非 Homebrew。** Brew 的 dotnet 依赖下载可能超时。

```bash
curl -fsSL https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh | bash
```

安装程序自动检测已安装的 Agent（Claude Code、Hermes Agent），并将 SKILL.md 写入相应的 skills 目录。安装路径位于 profile 的 Hermes home 路径下。

安装后创建全局 symlink：
```bash
sudo ln -sf $(find ~/.hermes -name officecli -type f | head -1) /usr/local/bin/officecli
```

验证：`officecli --version`

## MCP 注册

OfficeCLI 可以注册为任何 Agent 的 MCP server（支持 stdio 传输）：

- **Cursor**: `officecli mcp cursor`
- **Claude Code**: `officecli mcp claude`
- **Hermes Agent**: 需要手动配置（见下文）

`officecli mcp list` 显示各 Agent 的注册状态。

### Hermes Agent 配置

通过 `hermes config set` 添加 MCP server：

```bash
hermes config set mcp_servers.officecli.command /usr/local/bin/officecli
hermes config set mcp_servers.officecli.args.0 mcp
hermes config set mcp_servers.officecli.timeout 60
```

**已知问题**：`hermes config set` 可能生成非标准 YAML 格式（如 `args: {'0': mcp}` 而非 `args: [mcp]`）。通常功能不受影响，但如果 MCP server 未与 gateway 进程一起启动，需检查配置格式。

## 核心命令

| 命令 | 用途 |
|------|------|
| `create <file>` | 创建新文档（.docx/.xlsx/.pptx） |
| `add <file> <path>` | 在路径上添加元素（段落、行、幻灯片） |
| `set <file> <path>` | 修改元素属性（文本、格式） |
| `get <file> <path> --json` | 读取文档结构，支持 `--depth N` |
| `view <file>` | 通过内置 HTML 引擎渲染文档 |
| `view <file> screenshot -o <path>.png` | 将文档渲染为 PNG，供视觉检查 |
| `delete <file> <path>` | 删除元素 |

**支持的语言**：`--locale zh-CN` 用于中文文档。

## 使用模式与经验教训

### Word 文档

- 长段落添加可能超时。**改为短段逐段添加**，每段 1-3 句。
- 使用 `--prop alignment="CENTER"` 和 `--prop bold="true"` 进行格式化。
- `font_size` 属性可能不被 `add` 命令原生支持；必要时用 `set`。
- 使用 `view <file> screenshot` 生成视觉预览进行审校。

### Excel

- **公式引擎强大且可验证**：`AVERAGE`、`MAX`、`MIN` 全部内部求值。用 `get <file> <path> --json` 验证——查找 `"evaluated": true` 和 `"computedValue"`。
- 表头格式化：用 `--prop bold="true" --prop font_color="#FFFFFF" --prop fill="#4472C4"`。
- 属性名是 **`fill`**，不是 `fill_color`——后者会被静默忽略。
- 逐个单元格设置值（`set <file> "/Sheet1/A1" --prop text="..."`）比批量操作更可靠。
- 数值自动检测为 `Number` 类型；文本为 `String`。

### 公式验证检查清单

使用 `officecli get <file> "/Sheet1" --depth 3 --json` 并确认：
1. 统计行存在 `"formula"` 字段（如 `"formula": "AVERAGE(B2:B7)"`）
2. `"evaluated": true` 表示公式已执行
3. `"computedValue"` 匹配预期值

## BEFORE vs AFTER：Agent 工作流影响

| 维度 | BEFORE（无 OfficeCLI） | AFTER（有 OfficeCLI） |
|------|------------------------|------------------------|
| Word 创建 | 需要 Python-docx + 手动编码 | 自然语言 → CLI 命令 |
| Excel 公式验证 | 写入公式，需在 Excel 中打开验证 | CLI 内部求值，`evaluated: true` |
| 视觉审校 | 需用实际 Office 应用打开文件 | `view ... screenshot` 生成 PNG |
| 跨 Agent 共享 | 每个 Agent 独立安装 Python 库 | 单一 CLI 二进制，MCP 注册即用 |
| 中文支持 | 依赖库实现各异 | `--locale zh-CN` 原生支持 |
| 幻灯片创建 | 需要 python-pptx + XML 操作 | 直接 CLI 命令（参见 PPT 部分） |

## 更新历史

- 2026-07-13：基于 OfficeCLI v1.0.135 实测创建。涵盖安装、MCP 配置、Word/Excel 使用模式、公式验证、BEFORE-vs-AFTER 分析。来源于储能材料正极材料对比测试会话。

## 参考文件

- `references/cathode-comparison-test-data.md` — 正极材料对比完整数据集、公式列表、验证结果及关键发现
