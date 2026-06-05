# 微信公众号文章 → MP4 视频 实战 Recipe

## 来源

文章：《AI 取经记 01 | 给唐僧配上孙悟空：完成大模型的第一次 Tool Use 跃迁》
链接：https://mp.weixin.qq.com/s/-wCNNhrxisMDgQpB8Ktx3g
发布日期：约 2026 年 5 月
字数：~6000 字（正文）

## 抓取

```javascript
import { fetchSource } from './packages/cli/dist/fetch-source.js';
const result = await fetchSource('https://mp.weixin.qq.com/s/-wCNNhrxisMDgQpB8Ktx3g');
// { title: '《AI 取经记 01 | 给唐僧配上孙悟空：完成大模型的第一次 Tool Use 跃迁》',
//   markdown: '6013 chars', kind: 'article', truncated: false }
```

html-video 的 fetchSource 专为微信优化——提取 `#js_content` 内的正文，过滤掉导航/广告/样式。通用 web_extract 工具会因 SSRF 防护拒绝 `mp.weixin.qq.com`。

## Content-Graph（故事板）

```json
{
  "schemaVersion": 1,
  "intent": "explainer",
  "synopsis": "AI取经记01：以唐僧西行取经的比喻，讲解大模型Tool Use的核心概念...",
  "nodes": [
    { "id": "title_card", "kind": "text", "frameIntent": "hero", "durationSec": 5,
      "text": "AI 取经记 01\n给唐僧配上孙悟空\n完成大模型的第一次 Tool Use 跃迁" },
    { "id": "rwa_turn", "kind": "text", "frameIntent": "quote", "durationSec": 6,
      "text": "大半年追逐RWA宏大叙事\n最后发现一级市场真正需要的\n是一把铲除信息摩擦的铁锹" },
    { "id": "fos_intro", "kind": "text", "frameIntent": "hero", "durationSec": 7,
      "text": "上千场路演 · 三百家机构\n用AI硬化融资实战经验\n仓颉 FOS — AI驱动的资本架构师" },
    { "id": "tang_temple", "kind": "text", "frameIntent": "explain", "durationSec": 8,
      "text": "大模型 = 唐僧\n上知天文下知地理\n坐在蒲团上讲经布道\n但手无缚鸡之力，走不出结界" },
    { "id": "outside_temple", "kind": "text", "frameIntent": "explain", "durationSec": 9,
      "text": "Tool Use = 走出寺庙\n唐僧画符(JSON)→孙悟空执行→回来汇报\n暂停(Pause)→等结果→重入(Resume)" },
    { "id": "four_tools", "kind": "text", "frameIntent": "list", "durationSec": 10,
      "text": "仓颉FOS四大金刚\n1.宏观千里眼 2.孙悟空 3.巡山斥候 4.督军\n不是通用工具，是懂VC的垂直徒弟" },
    { "id": "outro", "kind": "text", "frameIntent": "outro", "durationSec": 5,
      "text": "西行才刚刚开始\n系统能不能主动反向访谈？\n能不能吞噬微信群脏数据？\n下一篇继续拆解" }
  ],
  "edges": [
    { "from": "title_card", "to": "rwa_turn", "kind": "sequence" },
    { "from": "rwa_turn", "to": "fos_intro", "kind": "sequence" },
    { "from": "fos_intro", "to": "tang_temple", "kind": "sequence" },
    { "from": "tang_temple", "to": "outside_temple", "kind": "sequence" },
    { "from": "outside_temple", "to": "four_tools", "kind": "sequence" },
    { "from": "four_tools", "to": "outro", "kind": "sequence" }
  ]
}
```

## 视觉风格

自定义暗色渐变 + 网格纹理风格（不使用内置模板）：

- 背景：`#0a0a1a` 深色底 + 紫色/粉色径向渐变 + 80px 网格纹理
- 字体：Inter Tight + Noto Sans SC（Google Fonts CDN）
- 渐变色文字：`linear-gradient(135deg, #818cf8, #e879f9)`
- 动画：`fadeUp` 关键帧（opacity 0→1, translateY 30→0），逐元素 staggered delay (.2s/.4s/.6s/.8s)
- 列表项：Flexbox 布局，数字标记用半透明紫底

## 渲染结果

```bash
node render-video.mjs
# → Bootstrap OK. Root: /tmp/html-video
# → Project created: proj_xxx
# → Content graph written
# → 7 frames written
# → Rendering MP4...
# → DONE! MP4: output.mp4
```

输出规格：
- 1920×1080, 60fps, H.264 (libx264, CRF 20), yuv420p
- 49 秒，2936 帧，6.6 MB
- 渲染耗时约 2 分钟（7 帧 × ~15 秒/帧）

## 关键决策

1. **不使用模板**：内置模板需要填写特定 inputs schema，对于长文解说不如自定义 HTML 灵活
2. **程序化调用 bypass Studio UI**：Studio 的 agent loop 需要外部 LLM agent，我们不配置时直接用 `bootstrap() + orchestrator API`
3. **帧时长分配**：根据内容密度手动设定（hero 5s, explain 8-9s, list 10s），而非均匀分配
4. **无配乐**：MiniMax API 需要额外 key，首批测试跳过

## 适用扩展

这个 recipe 可以直接复用于：
- 波总的其他「AI 取经记」系列文章
- 任何微信公众号文章（fetchSource 通用）
- 自定义品牌的解说视频（替换配色/字体）
