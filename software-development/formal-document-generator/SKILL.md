---
name: formal-document-generator
title: "正式外发文档生成器"
description: "生成排版精良的正式中文 Word (.docx) + PDF 文件。适合投资方案、合作协议、商务提案等正式外发场景。"
trigger: "当波总说'生成word'、'外发稿'、'正式文档'、'排版好的'、'给XX的方案'时"
---

# formal-document-generator — 正式外发文档生成

生成排版精良的正式中文 .docx + .pdf，适用于投资方案、合作协议、商务提案等场景。

## Phase 1: 确认内容与清洗

用户通常提供完整文字内容（或通过对话确认）。关键要素：
- 标题（方案名称、讨论稿/正式稿标注）
- 章节结构（共识前提 → 方案A/B → 通用条款）
- 关键数字（估值、出资额、比例 → 必须加粗）
- 页脚声明（可选）

### 1.1 内容清洗（用户要求"滤掉AI废话"时）

用户提供的文字如果带有微信/口语化包装（如"以下发给你注意内容""下面这版就是XX用的微信文字版""请注意哦"等），在生成文档前必须清洗：
- 删除所有会话式引导语和元说明（"可以，下面这版就是..."）
- 删除口语化后缀（"请注意哦""类似这样的词语要滤掉"）
- 保留正文结构的完整性（章节标题、列表、表格数据）

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

四条路径，按保真度优先级选择：

### 路径 A（首选）：docx2pdf — LibreOffice headless（所见即所得）

适用：已生成 DOCX 的正式外发文档。表格颜色、判断框底色、页眉页脚、页码域全保真。

```bash
docx2pdf 输入.docx [输出目录]   # wrapper：~/bin/docx2pdf（已内置 FONTCONFIG_FILE 修复）
```

⚠️ **macOS 中文字体坑（2026-08-27 实测）**：LO bundle 自带 fontconfig 但无 fonts.conf，headless 枚举不到系统字体 → PDF 中文全部空白（fallback 到希伯来字体 FrankRuhlHofshi）。必须设 `FONTCONFIG_FILE=/opt/homebrew/etc/fonts/fonts.conf`（brew fontconfig 配置含全部 macOS 字体目录）。`docx2pdf` wrapper 已内置此环境变量，裸跑 soffice 记得加。

验证：PDF 内嵌字体应含 PingFangSC/STHeiti（`python3 -c "import fitz;d=fitz.open(x);print({f[3] for f in d[0].get_fonts()})"`），而不是只有 LinuxLibertineG。

### 路径 B：DOCX → HTML → weasyprint（LO 不可用时的降级方案）

适用：内容以文字为主、无复杂表格时。

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

### 路径 B：DOCX → HTML → weasyprint（表格/格式复杂场景）

适用：已生成精致 DOCX（含表格、着色、复杂排版），需要保留全部格式时。

```bash
# Step 1: Convert DOCX to HTML
pandoc input.docx -t html -o /tmp/report.html

# Step 2: Inject CJK fonts into HTML, then render PDF
python3 -c "
from weasyprint import HTML
with open('/tmp/report.html') as f:
    html = f.read()
css = '''<style>
  @page { size: A4; margin: 2cm; }
  body { font-family: 'STHeiti', 'PingFang SC', 'Hiragino Sans GB', sans-serif; }
  h1, h2, h3 { font-family: 'STHeiti', 'PingFang SC', sans-serif; }
  table { font-family: 'PingFang SC', 'STHeiti', sans-serif; }
</style>'''
html = html.replace('</head>', css + '</head>')
HTML(string=html).write_pdf('output.pdf')
print('✅ PDF generated')
"
```

### 路径 C：Python fpdf2 直接生成（weasyprint 不可用时）

适用：weasyprint 因系统依赖缺失（`libgobject-2.0-0`）无法使用时。纯 Python 实现，零外部依赖。

```python
from fpdf import FPDF

FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"  # macOS 中文字体

pdf = FPDF('P', 'mm', 'A4')
pdf.add_font("zh", "", FONT_PATH)  # 常规
pdf.add_font("zh", "B", FONT_PATH)  # 粗体（使用同一字体文件）
pdf.set_auto_page_break(True, 20)

# 页面设置
pdf.add_page()
pdf.set_font("zh", "B", 22)
pdf.set_text_color(43, 87, 154)
pdf.multi_cell(0, 14, "文档标题", align='C')

# 正文
pdf.set_font("zh", "", 10.5)
pdf.set_text_color(40, 40, 40)
pdf.multi_cell(0, 6.5, "正文内容...")

# 项目符号列表 —— CRITICAL: 必须加 new_x="LMARGIN"
pdf.cell(6, 6, "•")
pdf.multi_cell(0, 6, "列表项文本", new_x="LMARGIN", new_y="NEXT")

# 有序列表
pdf.cell(8, 6, "1.")
pdf.multi_cell(0, 6, "有序项", new_x="LMARGIN", new_y="NEXT")

# 表格
pdf.set_fill_color(43, 87, 154)   # 表头背景色
pdf.set_text_color(255, 255, 255)  # 表头文字色
pdf.set_font("zh", "B", 9.5)
for cell in header_row:
    pdf.cell(col_width, 8, cell, border=1, fill=True, align='C')
pdf.ln()

# 数据行 — 交替行背景色
pdf.set_font("zh", "", 9.5)
for i, row in enumerate(data_rows):
    pdf.set_fill_color(240, 245, 252) if i % 2 else pdf.set_fill_color(255, 255, 255)
    pdf.set_text_color(40, 40, 40)
    for cell in row:
        pdf.cell(col_width, 8, str(cell), border=1, fill=True)

pdf.output("output.pdf")
```

### 字体选择

| 平台 | 中文字体 | 英文/数字字体 |
|------|----------|---------------|
| macOS | STHeiti（黑体）、PingFang SC | Helvetica Neue |
| macOS (现代) | PingFang SC（正文+标题，苹果系统默认） | SF Pro |
| Windows | SimHei（黑体）、SimSun（宋体） | Calibri |

**关键**: weasyprint 使用系统字体，不需要预先声明 @font-face。只需在 CSS 中指定 font-family 即可，weasyprint 自动查找系统安装的字体并嵌入 PDF。1.6MB 左右的 PDF 说明 CJK 字体已正确嵌入。

weasyprint 会输出 CSS warnings（text-rendering, overflow-x 等），**忽略即可**，不影响 PDF 输出。

完整可运行的 fpdf2 结构化文档参考实现见 `references/fpdf2-structured-doc-pattern.py`。

## Phase 3.5: 模板复用（高校成果转化项目讨论稿）

`templates/tech_transfer_discussion_template.py` — 14 部分骨架（2026-08-26 磁电项目固化）：
核心判断 / 四层壁垒 / 关键断点 / 三方向对比 / 一核一矛 / 公司化机制 / 团队设计 / 股权原则 /
首轮资金 / 90天计划 / 12个月三"第一次" / 终局 / 合作启动方式 / 15问 + 附录A退出测算 + 附录B图片清单。

适用：高校成果转化、教授创业、技术产业化方向性讨论（PRJ-030 电机、PRJ-031 飞车可直接套壳）。

流程：复制模板 → 替换 CONFIG（标题/月份/输出路径）→ 按注释把 XXX 占位换成实际内容 →
`python3 模板.py` 出 docx → `docx2pdf` 出 PDF。半小时出稿。

`scripts/render_engine.py` 为通用引擎（内容与排版分离，CONFIG+CONTENT 协议），新文档类型可基于它自定义。

## Phase 4: 输出

文件命名：`{方案名称}_{YYYYMMDD}.docx` / `.pdf`

输出到 `/Users/mac/Downloads/`，用 MEDIA 发送两个文件。

## Pitfalls

- **fpdf2 multi_cell 陷阱**：`multi_cell(0, h, text)` 执行后 x 位置会移到右边界（`w - rm`），导致下一次 `cell()` 从右边界开始，进而触发 `FPDFException: Not enough horizontal space to render a single character`。**必须在每次 `multi_cell` 后显式复位 x**：使用 `multi_cell(..., new_x="LMARGIN", new_y="NEXT")`。此规则同时适用于 `write_ul` / `write_ol` 等列表渲染方法。
- **fpdf2 中文字体**：用 `add_font("zh", "", ttc_path)` 注册后，`"B"` 粗体变体也指向同一 TTC 文件即可（fpdf2 不支持 TTC 内部选择具体 face，但使用同一文件能正常渲染）。废弃参数 `uni=True` 在 v2.5.1+ 可安全移除。

- **SyntaxError on Chinese quotes**: `\u201c明股实债\u201d` inside Python single-quoted strings WILL cause `SyntaxError: invalid syntax`. Use Unicode escapes `\u201c\u201d` or double-quote the outer string, or use the parts-list pattern.
- **DO NOT use docx built-in heading styles** — they override font settings. Build headings manually with `add_paragraph()` + custom runs.
- **`element.rPr.rFonts.set(qn('w:eastAsia'), ...)` is MANDATORY** — without it, Chinese text renders in default font on Windows, ruining the document for recipients.
- **LibreOffice 已装（2026-08-27）**：`docx2pdf` 为 PDF 首选（Phase 3 路径 A），weasyprint 保留为降级方案。macOS 下 soffice 必须带 `FONTCONFIG_FILE=/opt/homebrew/etc/fonts/fonts.conf`，否则中文全部空白（详见路径 A 坑说明）。
- **pandoc CSS warnings are harmless** — `text-rendering`, `overflow-x`, `gap` warnings from weasyprint do not affect output quality.
- **关键数字遗漏**：生成后人工检查一遍，确保所有估值/比例/利率都已加粗。
- **内部稿有红色标记**：机密印章和底部防盗警示用红色，区别于外发稿的灰色声明。
