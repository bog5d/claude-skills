---
name: industrial-brutalist-ui
description: 粗暴工业风预设 — 基于 taste-anti-slop 的高 VARIANCE 配置。粗野、不对称、反精致。适用于加密/Web3、独立音乐、实验性品牌。
version: 1.0.0
tags: [design, brutalist, industrial, ui, anti-slop, preset]
triggers:
  - brutalist
  - brutal
  - industrial
  - web3
  - crypto
  - experimental
  - raw
related_skills:
  - taste-anti-slop
  - claude-design
---

# industrial-brutalist-ui — 粗暴工业风预设

> 基于 `taste-anti-slop` 的子预设。先加载 `taste-anti-slop` 确立反模板纪律，再覆盖三刻度盘为粗暴配置。

## 刻度盘预设

```
DESIGN_VARIANCE:     9/10  (不对称、错位、断裂——纯粹的视觉张力)
MOTION_INTENSITY:    5/10  (机械式动效——不是流畅的 ease 曲线)
VISUAL_DENSITY:      5/10  (信息砸脸上，但不混乱)
```

## 风格 DNA

- **概念基石**: "Raw, not broken." — 低保真但不是做得烂。有意的粗糙，不是能力不足。网页看起来像被打印、复印、撕碎、再重新扫描的传单。
- **色彩**: 安全色 — `#ff0`、`#0ff`、`#f0f` + `#000` + `#fff`。只用 3–4 个高饱和撞色。灰度图转双色调（duotone）。背景可纯黑 `#000` 或纯白 `#fff`，不取中间值。
- **字体**: 等宽或 grotesk — `IBM Plex Mono` / `Space Mono` / `Syne` / `Schibsted Grotesk`。大号可变字号（`font-variation-settings` 拉满）。标题用全大写 + 超粗或超细权重，不取中间值。
- **布局**: 不对称是默认状态。元素之间用 `rotate(±1~3deg)` 故意错位。grid 可以有列宽不等的 `1fr 1.3fr 0.7fr`。元素可以叠在一起（`z-index` 碰撞 + `mix-blend-mode`）。
- **动效**: 不要标准的 power/ease 曲线。用 `steps(8)` 或 `ease: "steps(6)"` 做机械跳动。直接 `opacity: 0` ↔ `opacity: 1` 的硬切。甚至可以做 CRT 扫描线效果。

## 专属禁令（在 taste-anti-slop 基础上叠加）

| 违规 | 说明 |
|---|---|
| 流畅过渡 | 禁止 `power1-4.out`，只用 `steps()` / `"none"` / 硬切 |
| Bootstrap/Tailwind 默认外观 | 不用任何未重置的 utility class。所有颜色/间距必须是设计决策 |
| 圆角 | 一律 `border-radius: 0`。方角是工业的 |
| SVG icon 库 | 不能用 Feather/Heroicons。用自定义像素 icon 或 text-based marker |
| 对称布局 | 禁止 🤣 |

## 布局指令

- **网格**: 用 `display: grid` 但列宽不等，gap ≥ 60px。可以设置 `writing-mode: vertical-rl` 做竖排导航。
- **Hero**: 大号文字直给——字号 ≥ 120px，字重 900，可以搭配 `letter-spacing: -0.06em`。背景纯色或低分辨率纹理图。无渐变、无插图。
- **导航**: 竖排侧边或底部固定栏。文字全大写，12px，Mono。选中态 = 下划线（粗 3–4px）。
- **图片**: 永远是 `filter: grayscale(100%)` 或刻意的高反差黑白。可以用 `mix-blend-mode: difference` 叠在背景上。
- **边框**: `border: 2px solid #000` 或 `3px solid #fff`（等高反差）。故意不 align。
- **扫描线/噪点**: 可选伪元素 `::after { background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px); pointer-events: none; }`

## 检查清单

- [ ] 有任何两个元素是对称的吗？→ 错位一个
- [ ] 圆角全部 = 0？
- [ ] 字体来自 Mono/Grotesk 池？
- [ ] 配色仅 3–4 个高饱和撞色？
- [ ] 动效全是 steps/hard-cut？
- [ ] 没有图标库的预设 svg？
