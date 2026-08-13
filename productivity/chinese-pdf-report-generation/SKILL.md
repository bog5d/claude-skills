---
name: chinese-pdf-report-generation
description: 生成中文 PDF 报告时使用（fpdf2 已验证字体/表格/警示框）。
trigger: "生成中文 PDF 报告、归档 PDF、fpdf2 报告、壳评估/软著/正式文档 PDF 输出"
---

# 中文 PDF 报告生成（macOS + fpdf2）

覆盖：壳资源评估报告、软著材料、正式外发文档等一切需要**中文排版 PDF** 的场景。fpdf2 方案在本机已验证可用（python-docx→fpdf2 或直接 fpdf2 均可）。

## 已验证字体（2026-08 实测，别换）

- 标题/黑体：`/System/Library/Fonts/STHeiti Light.ttc`
- 正文/加粗：`/System/Library/Fonts/STHeiti Medium.ttc`
- 两者 `add_font` 均成功，中文全量渲染（含生僻字）

```python
pdf.add_font('HeiTi', '', '/System/Library/Fonts/STHeiti Light.ttc')
pdf.add_font('SongTi', '', '/System/Library/Fonts/STHeiti Medium.ttc')  # 名字叫 SongTi 但用 STHeiti Medium 文件
```

## 致命坑：Songti.ttc 对 Python 不可见

`/System/Library/Fonts/Songti.ttc`（63.8M）在 `ls` 里**看得到**，但 Python `os.path.exists()` 返回 False、`add_font` 抛 `FileNotFoundError`——macOS TCC/SIP 的进程可见性差异（`/usr/bin/ls` 能列，python3 打不开）。**直接用它必炸**，不要浪费时间排查，直接用 STHeiti Medium.ttc 做正文。

## 必做：emoji → ASCII 映射

fpdf2 不支持 Unicode emoji（✅❌⚠️🔴🟡），输出前替换：

```python
EMOJI_MAP = {
    '✅': '[OK]', '⚠️': '[!!]', '❌': '[X]', '🔴': '[HIGH]',
    '🟠': '[MED]', '🟡': '[LOW]', '🟢': '[CLEAR]', '❗': '[!]',
    '🚨': '[ALERT]', '①': '1)', '②': '2)', '③': '3)',
    '：': ':', '—': '-', '·': '.',
}
```

## 排版组件（模板已封装）

- 封面：大标题 + 公司名 + 评级结论 + 机密标识
- `h1/h2`：章节标题带下划线
- `verdict_box`：红底/黄底警示框（一票否决项、最终评级）
- `table`：深色表头 + 隔行变色 + 单格背景色标记（绿=OK/黄=WARN/红=HIGH）
- `multi_cell` 后需 `set_x(l_margin)` 复位光标（fpdf2 的 multi_cell 会把 x 留在文本末尾）

## 交付前验证（必做）

用 pymupdf 抽查，确认无漏页/乱码/字体缺字：

```bash
python3 -c "
import fitz
doc = fitz.open('报告.pdf')
print('pages:', len(doc))
t = ''.join(p.get_text() for p in doc)
for kw in ['章节关键词1', '关键数字', '公司名']:
    print(kw, '->', 'OK' if kw in t else 'MISSING')
"
```

## 模板

`templates/fpdf_report_generator.py` —— 完整可运行生成器（PDF 类 + 封面/表格/警示框/emoji 映射 + build() 骨架），复制后直接填内容。生成后存 `~/Downloads/<公司名>_报告.pdf` 并复制到 `~/.hermes/cache/documents/`（Telegram MEDIA 白名单）再交付。

## 陷阱

- 先 `python3 -c "import fpdf; print(fpdf.__version__)"` 确认已装；无则 `pip3 install fpdf2`
- `add_font` 失败先看是不是 Songti.ttc（见上），换 STHeiti 即可
- 表格列宽总和不要超过页面可用宽度（A4 边距 12mm 时约 186mm）
- 中文引号/破折号/特殊符号（——、·、①）统一走 EMOJI_MAP 或手写替换，fpdf2 对部分 unicode 标点会渲染为空白
