# XML 实体安全 — SVG 生成中的踩坑记录

> 会话日期: 2026-07-26
> 项目: 泽天智航 AI战略汇报（12页 PPT）

## 问题描述

`svg_to_pptx.py` 报错 `ParseError: undefined entity`，断点在对 `&yen;` 的解析。

XML 解析器（`xml.etree.ElementTree`）只识别 5 个内置实体，遇到任何 HTML 命名实体都会抛异常。

## 定位步骤

```bash
# 1. 确认是实体问题 — 定位到具体 SVG 和行号
grep -rn '&[a-zA-Z]\{2,\};' svg_output/ | grep -v '&amp;'

# 2. 列出所有不合法的 HTML 命名实体（排除 5 个合法 XML 实体）
grep -o '&[a-zA-Z]\{2,\};' svg_output/*.svg | grep -v -E '&(amp|lt|gt|quot|apos);' | sort -u
# 输出: &:yen;  (仅在 slide_04.svg 和 slide_09.svg)

# 3. 确认哪些文件有问题
grep -l '&yen;' svg_output/*.svg
# slide_04.svg  slide_09.svg
```

## 根因

生成脚本（`gen_slides_p1_p6.py` 和 `gen_slides_p7_p12.py`）的 f-string 中使用了 HTML 实体：

```python
# 错误的写法 — HTML 实体在 XML 中不合法
f'...&yen;{conservative}万...'

# 正确的写法 — 直接 Unicode 字符
f'...¥{conservative}万...'
# 或 XML 数值实体
f'...&#165;{conservative}万...'
```

## 修复

脚本中 4 处 `&yen;` → `&#165;` 替换后重跑，验证通过。

## 验证方法

```bash
# 确认修复后 SVG 中不含任何非法实体
grep -o '&[a-zA-Z]\{2,\};' svg_output/*.svg | grep -v -E '&(amp|lt|gt|quot|apos);'
# 无输出 = 通过

# 确认 svg_to_pptx.py 不再崩溃
$PY skills/ppt-master/scripts/svg_to_pptx.py projects/<project>/
# 输出: "PPTX exported: 12/12 slides" = 通过
```

## 预防

1. 生成 SVG 的 Python 脚本中 **永远不要使用 HTML 命名实体** — 直接嵌入 Unicode 字符
2. 写完后立即用 `grep -o '&[a-zA-Z]\{2,\};'` 扫描
3. 金额/货币符号用 `¥` (Unicode U+00A5) 而非 `&yen;`
4. 特殊空格用实际空格而非 `&nbsp;`
