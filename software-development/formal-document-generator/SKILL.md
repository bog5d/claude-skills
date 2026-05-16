---
name: formal-document-generator
title: "正式外发文档生成器"
description: "生成排版精良的正式中文 Word (.docx) + PDF 文件。适合投资方案、合作协议、商务提案等正式外发场景。"
trigger: "当波总说'生成word'、'外发稿'、'正式文档'、'排版好的'、'给XX的方案'时"
---

# formal-document-generator — 正式外发文档生成

生成排版精良的正式中文 .docx + .pdf，适用于投资方案、合作协议、商务提案等场景。

## Phase 1: 确认内容

用户通常提供完整文字内容（或通过对话确认）。关键要素：
- 标题（方案名称、讨论稿/正式稿标注）
- 章节结构（共识前提 → 方案A/B → 通用条款）
- 关键数字（估值、出资额、比例 → 必须加粗）
- 页脚声明（可选）

## Phase 2: 生成 DOCX（python-docx）

### 2.1 页面设置
```python
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

# 页边距：上下2.54cm，左右3.17cm（标准A4）
section.top_margin = Cm(2.54)
section.left_margin = Cm(3.17)

# 默认字体
style.font.name = '宋体'
style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
style.font.size = Pt(11)
```

### 2.2 字体层级
| 元素 | 字体 | 字号 | 样式 |
|------|------|------|------|
| 主标题 | 黑体 | 18pt | 加粗、居中 |
| 副标题(讨论稿) | 宋体 | 10pt | 灰色、居中 |
| 一级标题 | 黑体 | 15pt | 加粗 |
| 二级标题 | 黑体 | 13pt | 加粗 |
| 正文 | 宋体 | 11pt | 1.5倍行距、首行缩进0.74cm |
| 关键数字 | 宋体 | 11pt | **加粗** |
| 引用块 | 楷体 | 10pt | 斜体、灰色、左右缩进 |
| 条款编号 | 宋体 | 11pt | 加粗 |
| 页脚声明 | 楷体 | 9pt | 斜体、灰色、居中 |

### 2.3 关键数字加粗模式
所有估值、金额、比例必须加粗：
```python
r = p.add_run('7 亿元人民币')
r.bold = True
```

### 2.4 CRITICAL: parts-list 模式（防 SyntaxError）
**DO NOT** put Chinese curly quotes `\u201c\u201d` inside Python single-quoted strings — causes `SyntaxError: invalid syntax`. Use this pattern instead:

```python
def add_rich_para(parts):
    """parts = [("text", True/False), ...] — bold flag per segment"""
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.5
    for text, is_bold in parts:
        r = p.add_run(text)
        r.font.size = Pt(11)
        r.font.name = '宋体'
        r.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        if is_bold:
            r.bold = True

# Usage — NEVER inline Chinese quotes:
add_rich_para([
    ("核心逻辑：", True),
    ("想要普通股就按市场价（6亿）；想要特权就必须支付控制权溢价（7亿）。", False)
])

add_bullet([
    ("路径一（时间触发）：", True),
    ("投资满3年后，按\u201c本金+年化6%~8%利息\u201d强制赎回。", False)
])
```

The same pattern applies to `add_bullet(parts)`, `add_numbered(num, parts)` — all use the parts list.

### 2.5 内部稿变体
内部汇报稿额外需要：
- 红色机密标记：`\u3010机密 \u00b7 仅限董事长及核心决策层阅\u3011`，黑体 9pt，右对齐，RGB(200,0,0)
- 底部红色防盗警示：`\u2014 本件为内部决策参阅件，严禁外传 \u2014`，楷体 9pt，RGB(160,0,0)
- 二级标题可用楷体 13pt（与一级标题黑体形成视觉层级）

### 2.6 引用块
```python
p.paragraph_format.left_indent = Cm(1.0)
p.paragraph_format.right_indent = Cm(1.0)
# 楷体 10pt、斜体、灰色 RGB(60,60,60)
```

### 2.7 分隔线
```python
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('\u2014' * 6)  # —— em-dash separator
r.font.color.rgb = RGBColor(180, 180, 180)
```

## Phase 3: 生成 PDF

工具链：pandoc + weasyprint（LibreOffice 通常未安装，不依赖它）

```bash
pandoc input.md -o output.pdf --pdf-engine=weasyprint \
  --metadata title="文档标题" \
  --css=<(cat <<'CSSEOF'
body {
  font-family: "Songti SC", "SimSun", serif;
  font-size: 12pt; line-height: 1.8;
  max-width: 700px; margin: 0 auto; padding: 2em;
}
h1 { font-family: "Heiti SC", "SimHei", sans-serif; font-size: 18pt; text-align: center; }
h2 { font-family: "Heiti SC", "SimHei", sans-serif; font-size: 14pt; border-bottom: 1px solid #ddd; margin-top: 1.5em; }
h3 { font-family: "KaiTi SC", "KaiTi", serif; font-size: 12pt; }
strong { color: #000; }
blockquote {
  margin: 0.5em 1.5em; padding: 0.3em 1em;
  border-left: 3px solid #999; color: #444;
  font-family: "KaiTi SC", "KaiTi", serif; font-size: 10pt;
}
p { text-indent: 2em; margin: 0.4em 0; }
p:first-of-type, h1+p, h2+p, h3+p, blockquote p, li p { text-indent: 0; }
ul { padding-left: 1.5em; }
CSSEOF
)
```

weasyprint 会输出 CSS warnings（text-rendering, overflow-x 等），**忽略即可**，不影响 PDF 输出。

**不要在 .docx 上浪费时间转 PDF** — docx 转 PDF 需要 LibreOffice（brew install ~500MB），首次安装慢且 sandbox 可能受限。用 markdown → weasyprint 是更可靠的路径。

## Phase 4: 输出

文件命名：`{方案名称}_{YYYYMMDD}.docx` / `.pdf`

输出到 `/Users/mac/Downloads/`，用 MEDIA 发送两个文件。

## Pitfalls

- **SyntaxError on Chinese quotes**: `\u201c明股实债\u201d` inside Python single-quoted strings WILL cause `SyntaxError: invalid syntax`. Use Unicode escapes `\u201c\u201d` or double-quote the outer string, or use the parts-list pattern.
- **DO NOT use docx built-in heading styles** — they override font settings. Build headings manually with `add_paragraph()` + custom runs.
- **`element.rPr.rFonts.set(qn('w:eastAsia'), ...)` is MANDATORY** — without it, Chinese text renders in default font on Windows, ruining the document for recipients.
- **LibreOffice is a trap on macOS sandbox** — `brew install --cask libreoffice` takes 3-5 min and ~500MB. Just use markdown → weasyprint for PDF.
- **pandoc CSS warnings are harmless** — `text-rendering`, `overflow-x`, `gap` warnings from weasyprint do not affect output quality.
- **关键数字遗漏**：生成后人工检查一遍，确保所有估值/比例/利率都已加粗。
- **内部稿有红色标记**：机密印章和底部防盗警示用红色，区别于外发稿的灰色声明。
