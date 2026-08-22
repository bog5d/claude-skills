---
name: pptx-preview-render
description: 无 LibreOffice 时渲染 PPTX 某页成 PNG 预览。含颜色/对齐/比例三坑。
---

# PPTX Preview Render（PPTX → PNG 预览渲染）

## 触发场景
- 做完可编辑 PPTX 后，要给波总一张「渲染 PNG 预览」验收（交付四件套之一）
- 本机 **没有 LibreOffice / Keynote / PowerPoint**，`soffice`、`qlmanage`（只渲染第一页）都不可用
- 需要渲染**指定某一页**（不是第一页）的视觉效果

## 核心方法
`python-pptx` 解析 shape → 手写 SVG → `cairosvg` 转 PNG。无需任何 GUI 软件，cairosvg 在 Hermes venv 里已有。

脚本见 `scripts/render_pptx_preview.py`：

```bash
python3 render_pptx_preview.py <file.pptx> <slide_idx(0-based)> <out.png> [out.svg]
```

支持三类 shape：`PICTURE`（base64 data URI 嵌入）、`AUTO_SHAPE`（矩形/圆角矩形底板+线条）、`TEXT_BOX`（逐 run 渲染字体/大小/加粗/颜色）。

## 三个必踩的坑（已修复，勿回退）

1. **`str(RGBColor)` 返回 `RRGGBB` 无 `#` 前缀** — 直接塞进 SVG 的 `fill`/`font` 属性，cairosvg 会把整页文字当**黑色**渲染。必须统一补 `#%02X%02X%02X`（用 `_hex()` 处理 None/元组/字符串三种输入）。

2. **`text-anchor="middle"` 的 x 坐标是文本框中点，不是左边缘** — 用左边缘 x 配 `middle`，居中文字会整体偏移、视觉上像「截断」（如标题只显示后半截）。left→左边缘、center→中心、right→右边缘，三选一对齐。

3. **`add_picture` 同时给 width+height 会拉伸变形** — 只给其一按比例缩放。渲染脚本用 PIL 读真实尺寸算比例；排版时（python-pptx 里）也要保持：横向图（如卫星/星座 1.34:1）放进窄栏（3.9in）会按 `width` 算出超高，必须改成按 `height` 缩放 + 水平居中，否则图溢出页面底部。

## 验收自查
渲染 PNG 出来后，用 vision 模型快速核对：标题完整、无文字重叠、无溢出页面边界。注意 vision OCR 会把「垣信」读成「堪信」、「｜」（全角竖线 U+FF5C）读成「□」——这是 OCR 误读，不是 PPT 错误，别据此返工。

## 与 bundled skill 的关系
- `editable-pptx-delivery`（bundled，不可写）承载「交付纪律 + 结构自检门禁 + 素材定位」，它要求交付渲染 PNG 但没写「怎么渲染」——本 skill 补这一环。
- 结构自检走 `editable-pptx-delivery` 的 `pptx_structure_check.py`；渲染预览走本 skill 的 `render_pptx_preview.py`。
