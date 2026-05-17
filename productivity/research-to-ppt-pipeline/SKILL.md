---
name: research-to-ppt-pipeline
description: 研究 → PPT 完整管道。并行子Agent搜索 → 整合报告 → ppt-master生成PPTX → Telegram交付。适合"搜索研究某个主题并生成PPT"类任务。
---

# Research → PPT Pipeline

## 触发条件
用户说"搜索研究XX，生成PPT"时使用此技能。

## 工作流（5步）

### 第1步：并行研究（delegate_task batch模式）
将研究主题拆成2-3个方向，用delegate_task的tasks数组并行搜索。每个子Agent用terminal+file+web工具集。

示例：
```python
delegate_task(tasks=[
  {"goal": "搜索方向A...", "toolsets": ["terminal","file","web"]},
  {"goal": "搜索方向B...", "toolsets": ["terminal","file","web"]},
  {"goal": "搜索方向C...", "toolsets": ["terminal","file","web"]},
])
```

### 第2步：整合报告 + PPT素材
阅读子Agent输出，写一份source.md（PPT结构+内容），定义配色方案、页数、每页内容。

### 第3步：批量生成SVG

⚠️ **不要用execute_code写含中文的SVG** — execute_code沙箱对中文全角字符有编码问题（`SyntaxError: invalid character '，'`）。

正确做法：
1. 用write_file写一个Python脚本（如gen_slides.py），所有SVG通过函数生成
2. 用terminal执行该脚本

```bash
PY=/Users/mac/.hermes/hermes-agent/venv/bin/python3
$PY /Users/mac/ppt-master/projects/<project>/gen_slides.py
```

⚠️ **路径须知**：`~` 在Hermes profile环境下会展开到profile home而非用户真实home。必须用绝对路径：
- ppt-master: `/Users/mac/ppt-master/`
- venv python: `/Users/mac/.hermes/hermes-agent/venv/bin/python3`

### 第4步：ppt-master后处理 + 导出

```bash
PY=/Users/mac/.hermes/hermes-agent/venv/bin/python3
cd /Users/mac/ppt-master

# Step 1: finalize (圆角矩形→Path, 嵌入图片)
$PY skills/ppt-master/scripts/finalize_svg.py projects/<project>

# Step 2: 导出PPTX
$PY skills/ppt-master/scripts/svg_to_pptx.py projects/<project>
```

### 第5步：修复 & 重试

常见失败：`not well-formed (invalid token)` — SVG中`&`未转义。

```bash
# 查找未转义的 &
cd projects/<project> && grep -n ' & ' svg_output/*.svg | grep -v '&amp;'

# 修复：把 & 替换为 &amp;
# 然后重新跑 svg_to_pptx
```

### 第6步：交付

```bash
ls -lh projects/<project>/exports/*.pptx
```

在Telegram回复中加：`MEDIA:/Users/mac/ppt-master/projects/<project>/exports/<file>.pptx`

## 亮色系配色参考

```python
C = {
    "bg": "#FFFFFF",
    "primary": "#2563EB",   # 亮蓝
    "accent": "#F59E0B",    # 橙金
    "green": "#10B981",     # 翠绿
    "text": "#1E293B",      # 近黑
    "sub": "#64748B",       # 灰
    "card_bg": "#F8FAFC",
    "highlight_bg": "#EFF6FF",
    "divider": "#CBD5E1",
}
```

## SVG函数模板

```python
def T(x, y, content, size=16, color="#1E293B", anchor="start", bold=False):
    weight = 'font-weight="bold"' if bold else ''
    return f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}" {weight}>{content}</text>'

def R(x, y, w, h, fill=None, stroke=None, rx=0):
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}"']
    if fill: parts.append(f' fill="{fill}"')
    if stroke: parts.append(f' stroke="{stroke}" stroke-width="1"')
    if rx: parts.append(f' rx="{rx}"')
    parts.append('/>')
    return ''.join(parts)
```

## 避坑清单

1. **execute_code + 中文 = 编码错误** → 用write_file+terminal执行
2. **~ 路径在profile下重定向** → 用绝对路径`/Users/mac/`
3. **SVG中`&`未转义** → 全部用`&amp;`。用 `grep -n ' & ' svg_output/*.svg | grep -v '&amp;'` 检查
4. **finalize_svg必须跑在svg_to_pptx之前** → 否则圆角矩形渲染异常
5. **子Agent需要web工具集** → 搜索类任务必须加`\"web\"`
6. **Python函数名与常量冲突** → 批量生成SVG时，`H`/`W`/`F`/`D` 等单字母大写函数名会覆盖画布常量（`W=1280, H=720`），导致SVG出现 `<function H at 0x...>`。函数改用全小写（`hdr()`/`ftr()`/`tbar()`/`dv()`）。当svg_to_pptx报 `not well-formed: line 1, column 58` 时，打开SVG检查viewBox是否被函数对象污染。
