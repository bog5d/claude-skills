---
name: taste-anti-slop
description: Anti-template design layer for any AI-generated HTML (slides, pages, video frames). Brief inference → dial-driven design → forbidden-pattern filter → pre-flight check. Pairs with html-to-video / claude-design / popular-web-designs.
version: 1.0.0
tags: [design, html, anti-slop, taste, video, slides]
triggers:
  - html-to-video
  - make it look good
  - not AI-generated
  - design taste
  - anti-template
  - avoid slop
related_skills:
  - html-to-video
  - claude-design
  - popular-web-designs
  - article-to-video-production
---

# Taste Anti-Slop — 反模板设计层

> 这不是一个独立的设计技能。这是一个**叠加过滤器**——在任何 AI 生成 HTML 的任务之前加载，确保输出不带有 AI 模板味。
>
> 适用场景：公众号文章转视频幻灯片、Landing Page、演示文稿、产品页面。
> 不适用：Dashboard、数据表格、后台管理系统。

---

## 0. BRIEF INFERENCE（先读懂，再动手）

在写任何代码之前，先输出一行**设计判读**：

**“判读：{内容类型} 面向 {受众}，{风格关键词} 风格，倾向 {设计方向}。”**

示例：
- *“判读：公众号技术文章转视频，面向开发者，冷静克制风格，倾向 Linear-style 暗色 + Geist 字体 + 低动画。”*
- *“判读：品牌故事页面，面向消费者，温暖手工感，倾向 Notion-style 暖色调 + 衬线标题 + 留白。”*
- *“判读：产品 Landing Page，面向企业采购，专业可信风格，倾向 Stripe-style 紫蓝渐变 + 高对比度。”*

**如果需求模糊，只问一个问题，不要多问。** 能推断就推断，不追问。

---

## 1. 三刻度盘

设计判读之后，设三个 1-10 参数。所有布局/配色/动画决策由这三个参数驱动：

- **DESIGN_VARIANCE** (布局变化度)：1=完全对称，10=艺术性不对称
- **MOTION_INTENSITY** (动画强度)：1=静态，10=电影级动画
- **VISUAL_DENSITY** (信息密度)：1=极简留白，10=数据驾驶舱

**默认基线：7 / 4 / 3**（适合大部分文章转视频场景）

| 判读信号 | VARIANCE | MOTION | DENSITY |
|---|---|---|---|
| 极简 / 干净 / 冷静 / Linear-style | 5-6 | 2-3 | 2-3 |
| 品牌 / 高级感 / Apple-y / 奢侈 | 7-8 | 4-6 | 3-4 |
| 活泼 / 创意 / Awwwards / 实验性 | 9-10 | 7-9 | 3-4 |
| Landing / 营销页（默认） | 7-9 | 5-7 | 3-5 |
| 技术文章 / 教程 / 文档 | 5-6 | 2-3 | 4-6 |
| 视频幻灯片（公众号文章转视频） | 6-8 | 3-5 | 3-4 |

---

## 2. 反模板禁令（核心）

以下模式全部禁止，除非内容本身明确需要。

### 2.1 排版禁令

- **❌ Inter 作为默认字体。** 默认用 Geist / Outfit / Satoshi / Cabinet Grotesk。Inter 只在用户明确要求"中性/标准"时可用。
- **❌ 衬线作为默认。** "有创意感=衬线"是 AI 最明显的特征。衬线只在真正编辑/奢侈/出版场景下允许，且禁止 Fraunces 和 Instrument_Serif。
- **❌ em-dash `—` 在任何地方出现。** 标题、正文、注释、按钮、字幕一律禁止。这是 AI 设计的 #1 视觉特征。用句号、逗号、冒号替代。
- **❌ 斜体降部裁剪。** 斜体词含 `y g j p q` 时，行高至少 1.1，底部留 padding。
- **❌ 所有标题都用小型大写 eyebrow。** 每 3 个 section 最多 1 个 eyebrow。

### 2.2 配色禁令

- **❌ AI 紫/蓝光晕。** 禁止自动加紫色按钮发光、霓虹渐变。用中性底色（Zinc/Slate/Stone）+ 单一高对比度强调色。
- **❌ 一张页面两种强调色。** 选定一个强调色，全页统一。暖灰页面不会在第七屏突然出现蓝色 CTA。
- **❌ 对于"高级感消费品牌"自动用 beige+brass+espresso 配色。** 这个组合是 AI 的 #2 视觉特征。换为冷银/深绿/钴蓝+奶油/纯单色+单饱和跳色。
- **❌ `#000000` 纯黑。** 用 off-black（zinc-950 或 charcoal）。

### 2.3 布局禁令

- **❌ 居中 Hero + 渐变背景。** 当 VARIANCE > 4 时，用分屏/左对齐/不对称留白替代。
- **❌ 三列等大功能卡片。** 最明显的 AI 模板特征。用 2 列锯齿、不对称网格、横向滚动替代。
- **❌ 连续 3 屏以上用同一布局模式。** 8 屏页面至少用 4 种不同布局。
- **❌ Hero 区域塞入 tagline + trust strip + 价格提示 + 社交证明。** Hero 最多 4 个文本元素：eyebrow(可选) + 标题 + 副标题(≤20词) + CTA。
- **❌ `<br>` 断行制造"设计感"。** 标题应自然可读，不要用 `<br>` 强制分行。
- **❌ h-screen 全屏 Hero。** 用 `min-h-[100dvh]` 防止移动端地址栏导致跳动。
- **❌ Grid 对齐用 flexbox 百分比数学。** 用 CSS Grid `grid-cols-*`。

### 2.4 内容禁令

- **❌ Jane Doe / John Smith 等通用人名。** 用有地域感、真实感的名字。
- **❌ Acme / Nexus / SmartFlow 等模板品牌名。** 发明有语境感的品牌名。
- **❌ "Elevate"、"Seamless"、"Unleash"、"Next-Gen" 等填充动词。** 用具体动词。
- **❌ 虚假精确数字**（99.99%、4.1×、5.8mm）。除非数据来自真实 brief，否则用自然数。
- **❌ div 拼的假截图/假仪表盘/假终端。** 用真实截图、生成图片、或留占位符。
- **❌ `Trusted by / Quietly in use at` 等模板社交证明标题。** 用自然语言或直接省略。

### 2.5 幻灯片/视频帧专属禁令

- **❌ 每帧都一个布局。** 至少交替 3 种布局：全屏大字 → 分屏图文 → 卡片网格 → 引用大字 → 数据可视化。
- **❌ 标题超过 8 个词。** 视频帧上的标题必须一眼读完。
- **❌ 正文超过 25 个词/帧。** 视频不是阅读器，是视觉传达。
- **❌ 纯色背景 + 居中文字连续 3 帧。** 每帧需要视觉锚点：图片、图标、色块、数据或留白的节奏变化。
- **❌ 视频帧内出现 `<br>` 断行。** 视频帧的文字排版应完整、不依赖换行。
- **❌ emoji 出现在视频文本中。** 用图标库的 SVG icon 替代。

---

## 3. 设计纪律（正面指导）

### 3.1 字体

- 标题：`text-4xl md:text-6xl tracking-tighter leading-none`
- 正文：`text-base text-gray-600 leading-relaxed max-w-[65ch]`
- 推荐无衬线组合：Geist + Geist Mono / Satoshi + JetBrains Mono / Outfit + Inter
- **不要**把衬线字和无衬线字混在同一标题里（如 "and *spatial* design" 的混排套路）。

### 3.2 颜色

- 一个强调色。饱和度 < 80%。
- 中性底色 + 高对比单一强调色（Emerald / Electric Blue / Deep Rose / Burnt Orange）。
- 阴影用背景色调色，不用纯黑投影。
- 同一个项目里暖灰和冷灰不要混用。

### 3.3 布局

- **一张页面一个圆角系统。** 要么全直角(0)、全软角(12-16px)、全胶囊(full)。混用必须有明确规则且全页一致。
- **Hero 顶部间距最大 pt-24。** 超过就是设计 bug，不是"留白感"。
- **导航高度 ≤ 80px。** 桌面端必须单行，折行就是坏设计。
- **用卡片只在需要传达层级时。** 否则用 `border-t` / `divide-y` / 负空间分组。
- **列表项 > 5 个时换 UI 组件。** 不要默认 `<ul>` + `divide-y`，改用 2 列分组 / 卡片网格 / 横向滚动。

### 3.4 图片

优先级：
1. 图片生成工具（如果有）
2. `https://picsum.photos/seed/{描述性种子}/{w}/{h}`
3. 明确标记的占位符 `<!-- TODO: 1600x1200 hero image -->`

**即使是极简页面也需要真实图片。** 纯文本页面不是极简主义，是未完成品。

---

## 4. 幻灯片/视频帧特殊规范

当用于 `html-to-video` 管线时：

- **每帧传达一个想法。** 不要让一帧承载标题+三个要点+数据+引用。
- **标题区 + 内容区明确分离。** 48:52 或 40:60 的垂直分割比居中布局更有力。
- **视频帧需要安全区。** 关键内容放在中心 80% 区域内，边缘留 10% padding。
- **配色考虑视频播放环境。** 手机竖屏 (9:16) 时，暗色背景 + 亮色文字的对比度要求比网页高。
- **字体大小考虑手机观看。** 正文最小 18px（1080px 宽画布），标题最小 36px。
- **帧与帧之间要有视觉节奏。** 满字帧 → 留白帧 → 图文帧 → 大字帧交替。
- **首帧和尾帧特别对待。** 首帧是标题帧（最大字号，最少文字），尾帧是 CTA/二维码帧。
- **进度条/页码放在固定位置。** 所有帧统一位置，不要跳来跳去。

---

## 5. 交付前检查清单

**这不是可选的。每一项必须通过才能输出。**

- [ ] 设计判读已声明（Section 0）？
- [ ] 三刻度盘已设置且从判读推导？
- [ ] **零 em-dash `—`？** 标题、正文、注释、按钮、字幕——全页零出现。
- [ ] 强调色全页统一？没有第七屏换色的情况？
- [ ] 圆角系统全页一致？
- [ ] Hero 没有塞入 tagline + trust strip + 价格 + 社交证明？
- [ ] 没有三列等大功能卡片？
- [ ] 没有 AI 紫/蓝渐变默认配色？
- [ ] Inter 没有作为默认字体？（除非明确要求）
- [ ] 衬线没有作为默认字体？（AI 的 #1 字体特征）
- [ ] 没有 `h-screen`？（用 `min-h-[100dvh]`）
- [ ] 没有 div 拼的假截图？
- [ ] 没有 Jane Doe / Acme / 填充动词？
- [ ] 没有纯黑 `#000000`？
- [ ] 所有 CTA 按钮文字与背景对比度 ≥ WCAG AA（4.5:1）？
- [ ] [视频专属] 每帧一个想法？
- [ ] [视频专属] 标题 ≤ 8 词，正文 ≤ 25 词？
- [ ] [视频专属] 字体大小满足移动端可读？
- [ ] [视频专属] 帧与帧之间有视觉节奏变化？
- [ ] [视频专属] 首帧和尾帧专门设计？
- [ ] 已运行 `design-lint.py --preset <preset> <output.html>` 且无真实违规（误报已人工排除）？

**如果任一项不能诚实打勾，输出未完成。修好再交付。**

---

## 6. 自动化验证：design-lint.py

本 skill 自带一个 Python 自动化检查脚本。在任何 HTML 生成完成后，跑它来验证禁令是否被遵守：

```bash
python3 scripts/design-lint.py <output.html>                    # 自动推断预设
python3 scripts/design-lint.py --preset high-end <output.html>  # 强制高端预设
python3 scripts/design-lint.py --all <output.html>              # 全部规则
```

三种预设与风格子 skill 一一对应：
- `high-end` → `high-end-visual-design`
- `minimal` → `minimalist-ui`
- `industrial` → `industrial-brutalist-ui`

### 6.2 多预设并行生成流水线（已验证）

大规模风格对比测试的标准流程：

**Phase 1 — 数据采集**：用 firecrawl/web_extract 抓取真实数据，汇编为结构化 JSON（单文件，所有预设共用一个数据源）。

**Phase 2 — 并行生成**：用 `delegate_task` 并行跑 N 个预设（注意 max_concurrent_children 限制，超限时分批提交）。每个子任务读同一份数据 JSON，按各自预设的 SKILL.md 规范生成自包含 HTML。数据相同、风格不同——这是对比有效性的前提。

**Phase 3 — 质检矩阵**：对每个 HTML 跑 `design-lint.py`，汇总违规矩阵。关键步骤：逐条人工判定误报 vs 真实违规，而非盲信脚本输出。本次压测中 10/10 违规均为误报。

**Phase 4 — 汇总报告**：输出量化对比表（文件大小、动画类型、违规数、误报率） + 设计评级（风格多样性 / 反AI味 / 动画实现 / 误报识别 / 代币效率）。

已验证的预设组合：minimalist-ui + high-end-visual-design + industrial-brutalist-ui + popular-web-designs(Linear)。四份 HTML 应视觉上完全不可互认。

### 6.1 已知误报（pitfalls）

脚本是正则引擎，不是语义分析器。以下情况会触发误报，需人工判断：

- **Google Fonts `<link>` URL 含 "Inter" 字符串**：URL `?family=Inter:...` 会被 `no-banned-fonts` 误判，即使页面实际不用 Inter 字体。
- **径向渐变氛围光**：`radial-gradient` 用于非装饰性氛围背景时会被 `no-gradient` 误标。高端预设中的细节点缀渐变是允许的，大面积装饰渐变才违规。
- **CSS 类名含颜色关键字**：如 Tailwind 的 `text-purple-500` 类名可能触发颜色规则。

- **em-dash 来自外部数据源**：Wikipedia / API / 数据库抓取的内容中合法包含 em-dash `—`（如地名、标题），会被 `no-em-dash` 误标。数据源内容中的 em-dash 不应视为设计违规——只检查你手写的标题/注释/UI 文案。
- **box-shadow 为特定设计语言必需**：Linear.app / Stripe 等主流设计系统中卡片阴影是风格核心元素。`no-card-shadow` 规则在 Linear-style、Stripe-style 预设下应降低权重，仅在高 VARIANCE 预设下严格。
- **拖拽深度反馈的 `box-shadow`**：交互式元素（可拖拽卡片、抽屉面板）的 `box-shadow` 用于传达 z-index 层级和物理深度，是交互设计的一部分，不是静态卡片阴影。`no-card-shadow` 对此类场景为误报。
- **`backdrop-filter: blur()` 毛玻璃材质被 `no-gradient` 误标**：`backdrop-filter` 产生的模糊效果与 CSS gradient 无关，是材质设计（Apple HIG §Translucency）。`no-gradient` 规则的正则无法区分二者，需人工判定。
- **`no-purple-gradient` 误判蓝色为紫色**：规则的正则匹配范围过宽，`#3b82f6`（Tailwind blue-500）等蓝色调被误判为紫色渐变。蓝色按钮/强调色的 `box-shadow` 或 `background` 触发此规则时，核对实际色值后忽略。

遇到误报时，人工确认后忽略，不要为过 lint 而牺牲设计质量。

---

## 与其他 Skill 的配合

| 任务 | 加载顺序 |
|---|---|
| 公众号文章 → 视频 | `taste-anti-slop` → `html-to-video` |
| 品牌 Landing Page | `taste-anti-slop` → `claude-design` + `popular-web-designs` |
| 产品演示文稿 | `taste-anti-slop` → `reveal-ppt-skill` 或 `guizang-ppt-skill` |
| 文章配图/插图 | `taste-anti-slop` → `baoyu-article-illustrator` |
| A/B 设计质量对比 | `taste-anti-slop` → `design-lint.py`（对照组 + 新版） |

**规则：taste-anti-slop 总是在其他设计 skill 之前加载。** 它是过滤器，不是替代品。
