---
name: excel-notebooklm-convert
description: 加密/普通Excel→解密→多格式转换(MD/HTML/PDF) for NotebookLM。先确认意图再动手。
category: devops
trigger: 用户发送加密Excel+密码，或要求将Excel转成NotebookLM/手机可读格式。先问清楚仅去密码还是需要脱敏/清洗，不要自作主张。
---

# 加密 Excel → 解密 → 多格式转换

## 铁律：先确认意图

用户发加密文件+密码时，**必须先确认**：
1. 仅去密码？
2. 需要脱敏？
3. 需要 DDD 清洗？

**不要自作主张做脱敏。** 大多数情况用户就是想去掉密码。除非用户明确说"脱敏"，否则只解密。

## 解密

```bash
python3 -m pip install msoffcrypto-tool xlrd openpyxl fpdf2
```

```python
import msoffcrypto, io
dec = io.BytesIO()
with open(src, 'rb') as f:
    of = msoffcrypto.OfficeFile(f)
    of.load_key(password='...')
    of.decrypt(dec)
dec.seek(0)
with open(out_path, 'wb') as f:
    f.write(dec.getvalue())
```

## 格式转换（NotebookLM / 手机阅读）

### 推荐优先级

| 格式 | NotebookLM | 手机阅读 | 大小 |
|------|:---------:|:-------:|------|
| Markdown (.md) | ⭐最佳 | 一般 | 最小 |
| HTML (.html) | ✅支持 | ⭐最佳 | 中 |
| PDF (.pdf) | ✅支持 | ✅可读 | 大 |

### Markdown 生成

- 每个 Sheet 用 `## Sheet名` 做二级标题，`---` 分隔
- 跳过全空行
- 金额用 `{:,}` 格式化
- Excel 日期序列号 30000-60000 → `datetime(1899,12,30)+timedelta(days=serial)`

### HTML 生成

- 字体: `-apple-system, "PingFang SC", "Microsoft YaHei", sans-serif`
- 移动端: `font-size: 10-11px`, `white-space: nowrap`
- 斑马纹: `tr:nth-child(even) { background: #f9f9f9 }`
- 分页: `@media print { page-break-before: always }`

### PDF 生成

- **不要用 weasyprint** — macOS 缺 libgobject/pango
- 用 `fpdf2` + macOS 系统字体 `/System/Library/Fonts/STHeiti Light.ttc`
- A4 横版适合宽表格
- 中文字体: `pdf.add_font('CJK', '', font_path, uni=True)`
- 手动分行: 约 1.8mm/CJK 字符 at 6pt

## 陷阱

- msoffcrypto.encrypt() 签名是 `encrypt(password, outfile)`，password 在前
- xlrd 不支持加密文件，必须先解密
- xlrd 2.x 不支持 xlsx，只能读 xls
- openpyxl 不支持密码写入
- 金额扰动时注意排除 Excel 日期序列号 (30000-60000) 和年份 (2000-2099)
