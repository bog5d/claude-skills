---
name: editable-pptx-qa
description: 可编辑 PPTX 交付质检：越界检查、数据口径核验、字号文案规范。
version: 1.0.0
author: her-m2
license: MIT
---

# Editable PPTX QA（可编辑 PPT 质量门补充）

## 定位
bundled `editable-pptx-delivery` 承载「交付纪律 + 结构自检门禁 + 素材定位」，但它是 bundled 不可写。本 skill 承接波总后续追加的检查项，是它的 curator 增量层（与 `pptx-preview-render` 同模式：一个补渲染、一个补质检）。

## When to Use
- 可编辑 PPT 返修/交付前，跑完结构自检之后
- 波总明确点名「越界」「数据口径」「字号提升」「精简文案」时

## 1. 越界检查（元素不得超页面边界）
波总要求「任何元素不得超过页面边界」。16:9 页面 = 13.33 × 7.50 in。结构自检在「整页贴图」之外必须加越界维度：

```python
W, H = prs.slide_width/914400, prs.slide_height/914400
for sh in slide.shapes:
    r = sh.left/914400 + sh.width/914400   # right
    b = sh.top/914400  + sh.height/914400  # bottom
    if r > W + 0.01 or b > H + 0.01:
        print('越界:', str(sh.shape_type), round(r,2), round(b,2))
```

**根因**：横向图（如卫星/星座 1.34:1）放进窄栏时，若按 `width` 缩放会算出超高（bottom 溢出到 12in）。必须改按 `height` 缩放 + 水平居中（见 `pptx-preview-render` 坑 3）。布局写完跑一次越界检查，0 越界才算过。

## 2. 数据口径核验清单（不自行改写数字）
投资 BP 场景铁律：页内数字（已交付/独供/需求/单价/份额/市值）一律保留原始 BP 口径，**禁止 AI 推断补数**。凡涉及数字，交付时单列「数据口径核验清单」，每条 = 数据 + 来源页码，待 Codex/甲方确认事实口径后再逐条替换。

```
- UUV「客户侧独供 · 已交付 5+ · 单价 0.2–1 万」— BP 第6页
- 星载算力「交付 10+ · 单价 15–30 万」— BP 第5页
- 导航增强「需求 2000+」— BP 第5页
```

理由：AI 容易「顺手」补一个看起来合理的数字，投资人/尽调方逐条对口径，编一个就穿帮。宁可列清单等确认，也不自己定数。

## 3. 字号 / 文案规范
- 全页正文最低 **12.5–13pt**（10pt 太小投影看不清）；案例标题 **15–17pt**。
- 精简正文约 20%：优先「标题 + 一句结论 + 阶段/数字标签」，不堆长句。

## 与 bundled / curator 关系
- `editable-pptx-delivery`（bundled 不可写）：交付纪律 + 结构自检门禁 + 素材定位
- `editable-ppt-delivery`（bundled 不可写）：同主题重复 skill（待 curator 合并）
- `pptx-preview-render`（curator）：PPTX → PNG 渲染预览
- 本 skill（curator）：越界检查 + 数据口径核验 + 字号文案
