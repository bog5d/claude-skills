---
name: high-end-visual-design
description: 克制高级感预设 — 基于 taste-anti-slop 的中高 VARIANCE 配置。精致、层次分明、呼吸感。适用于奢侈品牌、SaaS 旗舰页、设计工作室。
version: 1.0.0
tags: [design, luxury, premium, ui, anti-slop, preset]
triggers:
  - luxury
  - premium
  - high end
  - elegant
  - sophisticated
  - flagship
related_skills:
  - taste-anti-slop
  - claude-design
---

# high-end-visual-design — 克制高级感预设

> 基于 `taste-anti-slop` 的子预设。先加载 `taste-anti-slop` 确立反模板纪律，再覆盖三刻度盘为高级感配置。

## 刻度盘预设

```
DESIGN_VARIANCE:     7/10  (有设计感但不跳脱——可识别的高端签名)
MOTION_INTENSITY:    5/10  (精致的微交互 + 滚动叙事，但不炫技)
VISUAL_DENSITY:      3/10  (信息有节奏地释放，呼吸感优先)
```

## 风格 DNA

- **概念基石**: "Density as luxury." — 高端感来自对空间和节奏的绝对控制。每一个像素的间距都是故意的。每一次滚动释放的少量信息，都是 precision。
- **色彩**: 深色背景基调（`#0a0a0a` ~ `#111`）+ 金/铜/象牙 accent（`#d4a853`、`#c9a96e`、`#e8d5b7`）。文字 `#f5f5f5` / `#999`。Accent 只在 5–10% 的画面中出现——少即贵。
- **字体**: Serif 标题 + Sans body — `Playfair Display` / `Cormorant Garamond` / `Bodoni Moda` × `Inter` / `DM Sans`。标题字号跨度大（36px ↔ 144px），字重用 Light（300）而非 Bold（700），这是高级感的核心差异。body 14–15px、letter-spacing 0.02em。
- **图片**: 必须是高质量摄影，深色/低光场景。可以用 `filter: brightness(0.85)` 压暗。图片边缘用径向羽化（`mask-image: radial-gradient(...)`）而不是矩形裁切。
- **动效**: 使用 `expo.out` 缓动（不是 `power`）做平滑 reveal。内容从下往上缓慢入场的 "unveil" 效果：`translateY(20px)` → 0，duration 0.8–1.2s，延迟 stagger 0.15s。滚动驱动的视差，速度不超过 0.3。

## 专属禁令（在 taste-anti-slop 基础上叠加）

| 违规 | 说明 |
|---|---|
| 高饱和度颜色 | 所有颜色饱和度 ≤ 40%（除了金属 accent） |
| flat design | 必须有深度：阴影、叠加、视差层次。至少 3 层 z-index |
| 粗体标题 | 标题字重用 Light/Regular（300-400），不是 Bold。靠字号和留白区分层级 |
| 边框/分割线 | 高级感不分隔——用间距和明度变化暗示边界。绝对不用 `<hr>` |
| 纯白背景 | 禁止。深色 > 米白 > 浅灰。纯白太廉价 |
| 等宽字体 | 禁止在任何正文/标题用 mono。高级 ≠ 技术 |
| 多色主题 | 仅三色：深基调 + 金属 accent + 浅字。不引入第四个 |

## 布局指令

- **网格**: 基于黄金比例或 √2 的模块化网格。12 列但实际只用 6–8 列，其余是留白。不对称卡片排列——图占 7 列、文占 4 列，错位排列。
- **Hero**: 全屏背景图/视频（深色/低亮度）+ 精短的 title 置中或靠左。字号 ≥ 72px，light 字重。副标题 18px，letter-spacing 0.08em，全大写。向下滚动的暗示用一道细线（不是箭头 icon）。
- **导航**: 顶部半透明（`backdrop-blur 效果`），logo 在左，4–5 项在右。文字 13px、letter-spacing 0.06em、全大写。
- **排版系统**: 需要 5 级字号：Hero 72–144px → H2 36–48px → H3 20–28px → Body 14–15px → 图注/Caption 11px。
- **CTA**: 按键不是圆角方块——是细线边框（`border: 1px solid accent`）+ 文字。hover 时内填充过渡（不是 scale）。

## 检查清单

- [ ] 仅 3 个颜色，且无纯白背景？
- [ ] 标题字重 = Light/Regular（不是 Bold）？
- [ ] 无 `<hr>` / border 分割线？
- [ ] 图片全部经过羽化/暗化处理？
- [ ] 动效全部 `expo.out`（不是 `power`）？
- [ ] 有至少 3 层 z-index 的视差/叠加层次？
- [ ] CTA 是细线边框，不是填充按钮？
