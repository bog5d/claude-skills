# macOS PDF 生成方案 — DOCX → PDF 转换

## 背景

`shell-company-analysis` 报告用 `delegate_task` 子代理生成。波总要求只出 PDF。

## 已验证方案：python-docx + fpdf2（推荐）

**成功率最高**。流程：

1. 用 `python-docx` 读取生成的 DOCX
2. 遍历段落和表格，提取文本内容和格式
3. 用 `fpdf2` 重新排版写入 PDF

```python
from docx import Document
from fpdf import FPDF

doc = Document('/path/to/report.docx')
pdf = FPDF()
pdf.add_font('HeiTi', '', '/System/Library/Fonts/STHeiti Light.ttc')
pdf.add_font('SongTi', '', '/System/Library/Fonts/Songti.ttc')
pdf.add_page()
# ... 逐段渲染 ...
pdf.output('/path/to/report.pdf')
```

字体路径（macOS）：
- 黑体：`/System/Library/Fonts/STHeiti Light.ttc` 或 `Hiragino Sans GB`
- 宋体：`/System/Library/Fonts/Songti.ttc` 或 `Songti SC`

## 失败方案记录

| 方案 | 失败原因 |
|------|---------|
| LibreOffice headless | 未安装 |
| pandoc → pdflatex | pdflatex 未安装 |
| pandoc → weasyprint | 超时（120s 无响应） |
| macOS cupsfilter | 无法识别 DOCX MIME |
| pip3 install weasyprint | 超时（依赖编译慢） |

## 注意事项

- `fpdf2` 不支持 Unicode emoji（✅❌⚠️🔴🟡）→ 替换为 ASCII：`[OK]` `[X]` `[!!]` `[HIGH]` `[MED]`
- 生僻字（如"玓瓅"）可能某些字体缺失字形 → 显示为空白方框，影响小
- `delegate_task` 生成大型报告可能超时（600s）→ 重试一次即可，第二次通常成功
