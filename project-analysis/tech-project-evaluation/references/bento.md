# Bento — 单 HTML 幻灯片工具

## 基本信息

- **仓库**: https://github.com/nyblnet/bento
- **许可**: MIT ✅
- **本地路径**: `/Users/mac/bento-slides/`
- **Stars**: 3.1k (截至 2026-07-31)
- **版本**: `slides/` v1.0.11

## 核心概念

单 HTML 文件 = 编辑器 + 播放器 + 演讲者模式 + JSON 文档数据。
打开即编辑，保存即自修改。对方浏览器打开就能演示。

## Build

```bash
cd /Users/mac/bento-slides/slides
npm install
npm run build:single   # → dist-single/Bento_Slides.bento.html (~660KB)
```

## 架构要点

- **format**: `bento/slides` v1，JSON 存储在 `<script type="application/bento+json" id="bento-doc">` 中
- **渲染**: Reveal.js 5.2.1 做演示导航层（翻页/过渡）
- **自研引擎**: anim.ts（morph/ken-burns/loop）、charts.ts（bar/line/pie/scatter，ECharts 兼容格式但自绘）、sync/crdt.ts（E2EE 协作）
- **依赖**: 仅 4 个运行时包（moveable, reveal.js, selecto, temml）
- **model.ts**: 996 行，完整的 TypeScript 文档模型定义

## AI 集成方式

JSON 文档存在 `#bento-doc` script block 中，Agent 直接编辑：
1. 读取文件，找到 `#bento-doc` 的 JSON
2. 修改 JSON（注意 `<` 转义为 `\u003c`）
3. 写回文件

有 Claude Code plugin（`/plugin marketplace add nyblnet/bento`）。
另有 `bento-slides` skill 可下载到 `~/.claude/skills/`。

## 与波总 PPT 栈的对比

| 维度 | guizang-ppt | reveal-ppt | ppt-master | **Bento** |
|---|---|---|---|---|
| 输出 | HTML 翻页 | HTML 翻页 | .pptx | 自修改 .bento.html |
| 风格 | 电子杂志/墨水 | 商务数据 | 原生 PPT | 模板+morph 动画 |
| 图表 | WebGL | Chart.js | PPT 图表 | 自研 charts-lite |
| AI | 无 | 无 | SVG→DrawingML | 原生 JSON 读写 |
| 分发 | 需托管 | 需托管 | 文件 | 单文件自包含 |
| 协作 | 无 | 无 | 无 | E2EE CRDT |

## 集成路线

1. 写 Hermes skill：输入内容 → 生成 .bento.html（注入 taste-anti-slop 预设）
2. 接入 bog-vocab-tracker / article-to-video 的 PPT 输出选项
3. 长期：提取 charts-lite 替代 reveal-ppt 的 Chart.js 依赖
