---
name: minimalist-ui
description: 极简编辑风预设 — 基于 taste-anti-slop 的低 VARIANCE 配置。克制、留白、排版驱动。适用于作品集、文档站、编辑类产品。
version: 1.0.0
tags: [design, minimal, ui, anti-slop, preset]
triggers:
  - minimalist
  - minimal
  - clean design
  - editorial
  - documentation UI
related_skills:
  - taste-anti-slop
  - claude-design
---

# minimalist-ui — 极简编辑风预设

> 基于 `taste-anti-slop` 的子预设。先加载 `taste-anti-slop` 确立反模板纪律，再覆盖三刻度盘为极简配置。

## 刻度盘预设

```
DESIGN_VARIANCE:     4/10  (干净信号，但不至于无聊)
MOTION_INTENSITY:    2/10  (只在关键交互出现，其余 fade)
VISUAL_DENSITY:      2/10  (大面积留白，信息稀疏)
```

## 风格 DNA

- **概念基石**: "Less, but better" — 每个元素必须有存在理由。删除一切非必要装饰。
- **色彩**: 严格单色 + 一个可控 accent。背景偏向 `#fafafa` ~ `#ffffff`，文字 `#1a1a1a` ~ `#4a4a4a`。accent 饱和度不超过 30%（低饱和且克制）。
- **字体**: "EDITIONAL" 池 — 优先 `IBM Plex Serif` / `Source Serif 4` / `Newsreader`。body 用 `system-ui` 或 `Inter` 的最小字号（14–15px，比常规小一号）。标题用 `letter-spacing: -0.02em`。
- **留白**: 这是你的主武器。section 间距 ≥ 120px，卡片/段落间距 ≥ 48px。用负空间区分层级，别用 border/divider。
- **动效**: 仅入场的 fade-up（`translateY(8px)` + `opacity 0→1`，duration 0.4–0.6s，ease `power3.out`）。hover 只做微小的颜色/opacity 变化，不做 scale/阴影。**绝对不要**连续的滚动触发动画链。

## 专属禁令（在 taste-anti-slop 基础上叠加）

| 违规 | 说明 |
|---|---|
| 卡片阴影 | 极简无需卡片，用留白+对齐区分。最多 `border-bottom: 1px solid #eee` |
| 渐变色 | 背景/按钮/标题一律纯色。极简不配渐变 |
| 圆角 > 6px | 输入框 4px，按钮 2-4px。不可见圆角 |
| em-dash 滥用 | 铁律不变。尤其是排版站点 |
| 大号 emoji/icon | 不出现 >40px 的装饰 icon / emoji |
| 背景色块 | 每个 section 之间不换背景色，维持统一的白色/浅灰 canvas |

## 布局指令

- **网格**: 单列正文区 640–720px 居中。最大宽度约束后左对齐。
- **Hero**: 无渐变、无插图、无 Lottie、无粒子。一句话 + 副标题 + 可能一个 CTA。Hero 高度 ≤ 60vh。
- **导航**: 极简横栏或汉堡菜单。透明/白色背景，底部 1px border。仅 3–5 项。
- **图片**: 黑白或低饱和度。图片包含在 1px `#e0e0e0` border 中。没有视差、lightbox hover 效果。

## 检查清单

- [ ] 任何删除后不影响理解的元素已删除？
- [ ] 全页仅 1 个 accent color？
- [ ] 没有卡片 shadow、没有渐变、没有可见圆角？
- [ ] 正文区 ≤ 720px？
- [ ] 动效仅限于 fade-up 入场？
