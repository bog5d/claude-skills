---
name: chinese-document-generation
description: 正式中文 Word/PDF 文档生成进阶（TOC域/页码/底纹/CONTENT驱动/weasyprint PDF）。
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [docx, pdf, weasyprint, python-docx, 正式文档]
    related_skills: [formal-document-generator, docx, chinese-pdf-report-generation]
---

# 中文正式文档生成进阶（python-docx + weasyprint）

## When to Use
- 用户要求生成**正式中文 Word 文档**（讨论稿/方案书/尽调报告/合作协议）且需要**自动目录、页眉页脚、页码**时
- 文档含 **10 张以上表格**（对比表/验证表/行动表/测算表），需要判断框、待核实提示框等结构化视觉元素时
- 需要 **docx → PDF** 且本机无 LibreOffice 时
- 已加载 bundled `formal-document-generator` / `docx` 但发现缺 TOC/页码/底纹/weasyprint 能力时（本技能是其不可编辑内容的补充）

> 本技能承载 **bundled `formal-document-generator` / `docx` 之外验证过的进阶技术**（那两个 bundled 技能后台不可编辑，基础排版规范请仍以它们为准）。2026-08-26 实测：14 部分 + 27 表格的《磁电复合材料技术产业化路径与公司化机制讨论稿 V0.1》全流程。

## 触发场景
- 需要**自动目录、页眉页脚、页码**的正式 .docx（讨论稿、方案书、尽调报告）
- 文档含 **10+ 张表格**（四层壁垒表、对比表、行动表、敏感性测算表）
- 需要 docx → PDF（保留表格样式，无 LibreOffice）

## CONTENT 驱动大文档模式（内容与渲染分离）
避免巨型单脚本难维护：
- `xxx_content.py`：`CONTENT` 列表，每项元组 `("h1"/"h2"/"h3"/"p"/"b"/"n"/"callout"/"warn"/"table"/"flow"/"pb"/"tag", ...)`；用 `def h1(t): CONTENT.append(("h1", t))` 辅助函数写作。
- `xxx_render.py`：渲染器遍历 CONTENT 生成 docx，统一管页面/样式/页眉页脚/底纹。
- 渲染器骨架见 `scripts/render_content_docx.py`（可直接复用：CALLOUT/WARN/TABLE/FLOW/PAGEBREAK/TAG 全套）。

## 关键技巧（均实测）
1. **TOC 自动目录域**：标题必须用内置 Heading 样式（**显式覆盖其 font** 的 name/eastAsia/size/color，TOC 可识别且字体受控）；在 run 上依次追加 `w:fldChar(begin)` → `w:instrText('TOC \\o "1-2" \\h \\z \\u')` → `w:fldChar(separate)` → 占位文本（"打开文档后右键→更新域"）→ `w:fldChar(end)`。
2. **页码域**：页脚 run 内嵌 `' PAGE '` / `' NUMPAGES '` 的 fldChar begin/end（"第 X 页 / 共 Y 页"）。
3. **表格单元格底纹**：`tcPr` 追加 `w:shd(val=clear, color=auto, fill=HEX)`。配色：表头深蓝 `2B579A` 白字、隔行 `F2F2F2`、判断框浅蓝 `DCE6F1`、待核实浅橙 `FDE9D9`。判断框/提示框 = 1×1 表格 + 底纹 + 主题色标题。
4. **表格列宽**：仅设表头不生效，需对**每行** `row.cells[i].width = Cm(x)`。
5. **中文字体**：`rFonts.set(qn('w:eastAsia'), 'PingFang SC')` 必设（否则 Windows 上中文回退默认字体）；标题黑体（STHeiti/PingFang 加粗），正文 10.5-11pt，表格 ≥9pt。
6. **页眉**：加下边框线（pBdr/w:bottom）更正式。

## DOCX → PDF（macOS，无 LibreOffice，已验证）
weasyprint 在 Hermes venv 内（系统 pip 无权限装包时用它）：
```bash
export PATH=~/.hermes/hermes-agent/venv/bin:$PATH
pandoc "输入.docx" -o "输出.pdf" --pdf-engine=weasyprint --css=/tmp/docstyle.css
```
CSS 要点：`@page { size: A4; margin: 2.2cm 2.3cm; }`；`table { border-collapse: collapse; width: 100%; font-size: 9pt; }`；`th { background: #2B579A; color: white; }`；`tr:nth-child(even) td { background: #F2F2F2; }`。weasyprint 的 `overflow-x` 警告可忽略。已验证输出 ~550KB 带表格样式 PDF。

## 交付规范（波总偏好）
- docx + pdf 双份，输出到 `~/Downloads/`，MEDIA 发送两个文件
- 附 ≤500 字制作说明（核心判断/推荐方向/待核实内容/后续最值得生成的图片）
- 文档内信息状态标注：【已有材料】【公开可证】【待核实】【方案假设】——波总对外讨论稿的硬性要求
- 自检：无 AI 腔（综上所述/赋能/生态闭环/强强联合/未来可期）、不把待核实写成事实、内部判断（"没方案不谈"等）绝不入稿、数字自洽

## Pitfalls
- **内置 Heading 样式 vs 自定义段落**：需要 TOC 时必须用内置 Heading（覆盖字体）；小文档无 TOC 才用纯自定义段落。bundled formal-document-generator 的"不用内置 heading"警告仅适用于后者。
- python-docx 读回自检：`doc.paragraphs` 里 `p.style.name == 'Heading 1'` 可枚举结构，`doc.tables` 数表格——交付前跑一遍。
- 中文弯引号放 Python 单引号字符串会 SyntaxError：用 `\u201c \u201d` 转义或双引号外层。
