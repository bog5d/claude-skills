---
name: html-video-workflow
description: 使用 nexu-io/html-video 将文章/内容转为带动画的 MP4 视频。支持微信公众号文章抓取、content-graph 故事板、Playwright+ffmpeg 本地渲染。Apache-2.0，零 API 费用。
---

# html-video — HTML 驱动视频生成工作流

## 概述

html-video 是 nexu-io 团队开发的 HTML→Video meta-layer。核心理念：**Agent 写 HTML → 本地 Chromium 录制 → ffmpeg 编码 MP4**。全链路本地运行，零 API 调用费用。

与 Remotion 的关系：**互补，非替代**。
- Remotion：精雕细琢的动画工作室（React 组件、粒子特效、品牌 Intro）
- html-video：快速出片的自动化产线（HTML+CSS、Agent 驱动、模板化）

## 触发条件

用户说"把文章做成视频"、"html-video"、"HTML 转视频"、"公众号文章生成视频"、"content-graph"、"给这个链接做视频"

## 快速开始

```bash
cd /tmp
git clone https://github.com/nexu-io/html-video.git
cd html-video
pnpm install
pnpm -r build

# 环境检查
node packages/cli/dist/bin.js doctor

# 启动 studio（可选，Web UI）
node packages/cli/dist/bin.js studio --port 3090
```

## 核心概念

### 渲染管线
```
文章链接 / 文本
    → fetchSource() 抓取→Markdown
    → Agent 生成 content-graph（故事板 JSON）
    → Agent 生成逐帧 HTML
    → Playwright Chromium 逐帧录制 webm
    → ffmpeg 编码 mp4 + concat 拼接
    → 最终 MP4
```

### Content-Graph 格式（RFC-06）

```json
{
  "schemaVersion": 1,
  "intent": "explainer|promo|data-viz|comparison|single-frame",
  "synopsis": "一句话概括视频主题",
  "nodes": [
    {
      "id": "scene_id",
      "kind": "text|entity|data",
      "label": "场景名",
      "frameIntent": "hero|quote|explain|list|outro",
      "durationSec": 5,
      "text": "该帧显示的文本内容"
    }
  ],
  "edges": [
    { "from": "scene_1", "to": "scene_2", "kind": "sequence" }
  ]
}
```

边缘类型：
- `sequence`：软顺序偏好
- `dependency`：硬依赖（B 必须在 A 之后）
- `contrast`：对比关系

### 帧 HTML 要求
- 自包含 HTML 文件，内联 CSS + JS
- 目标分辨率：1920×1080（默认）
- 动画用 CSS @keyframes 或 GSAP
- 字体引用 CDN（Google Fonts）
- 文件放在项目 `frames/` 目录

## 程序化使用（跳过 Studio UI）

```javascript
import { bootstrap } from './packages/cli/dist/context.js';

const { orchestrator } = await bootstrap({ cwd: '/path/to/html-video' });

// 1. 创建项目
const project = await orchestrator.create({ name: '视频标题', intent: 'explainer' });

// 2. 写入故事板
await orchestrator.writeContentGraph(project.id, contentGraph);

// 3. 逐帧写入 HTML
for (const node of graph.nodes) {
  await orchestrator.writeFrameHtml(project.id, node.id, frameHtml);
}

// 4. 渲染 MP4
const result = await orchestrator.exportMp4({
  projectId: project.id,
  onProgress: (pct, stage) => console.log(`${pct}% ${stage}`)
});
// → result.outputPath
```

## 文章抓取

html-video 内置 `fetch-source.ts`，**专为微信公众号优化**：

```javascript
import { fetchSource } from './packages/cli/dist/fetch-source.js';
const result = await fetchSource('https://mp.weixin.qq.com/s/...');
// → { title, markdown, kind: 'article', truncated: bool }
```

关键实现：
- 微信文章：提取 `#js_content` div 内容
- 通用文章：提取 `<article>` / `<main>` / `<body>`
- GitHub 仓库：通过 REST API 拉取 README + 目录结构
- 内建 SSRF 防护（拒绝私有 IP/内网地址）

## 模板体系

21 个内置模板（Apache-2.0），按场景分类：
- **标题/封面**：frame-glitch-title, frame-liquid-bg-hero, frame-light-leak-cinema
- **数据可视化**：frame-data-chart-nyt, frame-pentagram-stat
- **产品宣传**：frame-product-promo, frame-product-promo-30s
- **解说**：frame-decision-tree, frame-takram-organic
- **结尾**：frame-logo-outro
- **特效**：vfx-text-cursor

查询模板：`node packages/cli/dist/bin.js search-templates --intent "github stars" --top 3`

## 自定义帧 HTML 最佳实践

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: 'Inter Tight','Noto Sans SC',system-ui,sans-serif;
    background: #0a0a1a; color: #f0f0f0;
    width: 1920px; height: 1080px; overflow: hidden;
    display: flex; align-items: center; justify-content: center;
  }
  /* 渐变背景 */
  .bg-grad {
    position:absolute; inset:0;
    background: radial-gradient(ellipse at 30% 20%, rgba(99,102,241,.35) 0, transparent 70%),
                radial-gradient(ellipse at 70% 80%, rgba(236,72,153,.25) 0, transparent 70%);
  }
  /* 网格纹理 */
  .grid {
    position:absolute; inset:0;
    background-image: linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),
                      linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);
    background-size: 80px 80px;
  }
  /* 文字渐入动画 */
  @keyframes fadeUp {
    from { opacity:0; transform:translateY(30px); }
    to { opacity:1; transform:translateY(0); }
  }
  .anim { animation: fadeUp .8s ease-out both; }
  .d1 { animation-delay: .2s; }
  .d2 { animation-delay: .4s; }
  .d3 { animation-delay: .6s; }
  .d4 { animation-delay: .8s; }
  /* 渐变色文字 */
  .accent {
    background: linear-gradient(135deg, #818cf8, #e879f9);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
</style>
</head>
<body>
  <div class="bg-grad"></div><div class="grid"></div>
  <div class="content">
    <div class="tag anim d1">标签</div>
    <h1 class="anim d2"><span class="accent">标题</span></h1>
    <p class="anim d3">副标题</p>
  </div>
</body>
</html>
```

## 输出规格

- 默认：1920×1080, 60fps, H.264 (libx264, CRF 20), yuv420p
- 文件大小估算：~1.3 Mbps，49 秒 ≈ 6.6 MB
- 渲染耗时：每帧约 10-15 秒（Playwright 录制 + ffmpeg 编码）
- 支持 30fps 和多种宽高比（16:9, 9:16, 1:1）

## 环境要求

- Node.js >= 20
- pnpm >= 9
- ffmpeg（`brew install ffmpeg`）
- Playwright Chromium（`npx playwright install chromium`，pnpm install 自动处理）

## Pitfalls

- **adapter-hyperframes 不是 stub**：CLAUDE.md 中的过时注释说它是 stub，但实际代码 (render.ts) 是完整的 Playwright+ffmpeg 实现。以实际代码为准。
- **web_extract 无法抓微信文章**：`mp.weixin.qq.com` 被 SSRF 防护拦截。用 html-video 内置的 `fetchSource()` 替代。
- **模板的 sourcePath 必须存在**：渲染前检查帧 HTML 文件是否在磁盘上，否则 `Source HTML not found` 错误。
- **帧时长要覆盖动画**：渲染器会自动探测 CSS animation-duration 并延长录制时间（caps at 30s/frame），但建议手动设合理 durationSec。
- **无音频时只有视频流**：不加 soundtrack 的 MP4 只有 video stream，在部分播放器可能无法播放。Telegram 兼容。
- **studio 的 agent 需要外部 LLM**：studio 内置 agent loop 但需要本地 coding agent（Claude Code/Cursor/Codex/Hermes）或 Anthropic API key。无 agent 时走程序化路线（手动生成 content-graph + HTML）。
- **pnpm workspace 依赖**：必须在 repo 根目录运行，程序化调用用 `bootstrap({ cwd: repoRoot })`。

## 集成方向

1. **公众号文章 → 视频**：文章链接 → fetchSource 抓取 → 我（Agent）生成 content-graph + HTML → 渲染
2. **品牌模板定制**：在 templates/ 下新增自定义模板，含 template.html-video.yaml
3. **配乐**：MiniMax API 生成背景音乐 + TTS 旁白（需 API key）
4. **批量生产**：循环多篇文章 → 生成视频合辑

## 参考

- 项目：https://github.com/nexu-io/html-video
- 姊妹项目：html-anything（静态 HTML 模板）、open-design（设计 agent）
- 引擎：Hyperframes（当前唯一适配器），Remotion/Motion Canvas 计划中
- **`references/wechat-article-recipe.md`** — 微信文章→视频完整 recipe（含 content-graph + 帧结构 + 渲染结果）
- **`templates/render.mjs`** — 可复用的程序化渲染脚本模板
