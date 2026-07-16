# Apple Design — 兼容性说明

## 与现有审美栈的关系

`apple-design` 与 `taste-anti-slop` 及其他设计类 skill 是**正交互补**关系。

### 职责分层

```
Layer 4: 动画执行层     → gsap-animation（GSAP 实现）
Layer 3: 动画审计层     → improve-animations（质量审查 + 路线图）
Layer 2: 动效物理层     → apple-design（弹簧参数、动量、可中断性、材质）
Layer 1: 静态审美层     → taste-anti-slop（色彩、字体、布局、反AI味禁令）
```

### 零冲突验证

| 维度 | taste-anti-slop | apple-design | 冲突？ |
|---|---|---|---|
| 字体 | Geist 优先，禁 Inter 默认 | SF Pro / 光学尺寸 letter-spacing | 可组合 |
| 颜色 | 单一强调色，禁紫色渐变 | 毛玻璃 backdrop-filter | 毛玻璃是材质不是颜色 |
| 布局 | 禁三列等大卡片 | 空间一致性（镜像路径） | 配合使用 |
| 阴影 | no-card-shadow（部分预设严格） | 拖拽深度反馈 shadow | lint 可能误报 |
| 渐变 | no-gradient 禁大面积装饰 | backdrop-filter: blur() | lint 可能将 blur 误标为 gradient |

### 推荐加载顺序

```
taste-anti-slop → apple-design → gsap-animation
```

`taste-anti-slop` 先设审美底线，`apple-design` 加物理手感，`gsap-animation` 做实现。

### 适用格式矩阵

| 输出格式 | taste-anti-slop | apple-design 动效 | apple-design 排版 |
|---|---|---|---|
| HTML 页面 | ✅ 全部 | ✅ 全部 | ✅ 全部 |
| HTML PPT (Reveal.js/Guizang) | ✅ 全部 | ✅ 全部 | ✅ 全部 |
| 视频帧 (html-to-video) | ✅ 全部 | ❌ 无交互 | ✅ 字距规则 |
| Word / PDF | ❌ 不适用 | ❌ 无交互 | ✅ 字距规则 |

### 已知限制

1. **skill_view 不识别新安装的 skill** — 需重启 Hermes gateway 重新索引
2. **design-lint.py 误报** — no-purple-gradient 将 #3b82f6 误判为紫色；no-gradient 将 backdrop-filter 误判为渐变；no-card-shadow 将拖拽深度反馈误判为静态卡片阴影
