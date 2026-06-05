/**
 * html-video 程序化渲染脚本
 * 
 * 用法：修改下面的 graph 和 frames 对象，然后运行：
 *   cd /path/to/html-video && node render.mjs
 * 
 * 输出：.html-video/projects/<project-id>/output-<timestamp>.mp4
 */

import { bootstrap } from './packages/cli/dist/context.js';

const { orchestrator, projectRoot } = await bootstrap({ cwd: new URL('.', import.meta.url).pathname });

// ── 1. 创建项目 ──
const project = await orchestrator.create({
  name: '视频标题',
  intent: 'explainer'  // explainer | promo | data-viz | comparison | single-frame
});
console.log(`Project: ${project.id}`);

// ── 2. 定义故事板 ──
const graph = {
  schemaVersion: 1,
  intent: 'explainer',
  synopsis: '一句话描述视频主题',
  nodes: [
    // 按播放顺序排列（sequence edges 会自动确定顺序）
    { id: 'scene_1', kind: 'text', label: '场景1', frameIntent: 'hero', durationSec: 5,
      text: '场景1的文本内容' },
    { id: 'scene_2', kind: 'text', label: '场景2', frameIntent: 'explain', durationSec: 8,
      text: '场景2的文本内容' },
    // ... 更多场景
  ],
  edges: [
    { from: 'scene_1', to: 'scene_2', kind: 'sequence' },
    // ... 更多边
  ]
};

await orchestrator.writeContentGraph(project.id, graph);

// ── 3. 定义视觉样式 ──
const CSS = `
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{
  font-family:'Inter Tight','Noto Sans SC',system-ui,sans-serif;
  background:#0a0a1a;color:#f0f0f0;
  width:1920px;height:1080px;overflow:hidden;
  display:flex;align-items:center;justify-content:center;
}
.bg-grad{
  position:absolute;inset:0;
  background:radial-gradient(ellipse at 30% 20%,rgba(99,102,241,.35) 0,transparent 70%),
             radial-gradient(ellipse at 70% 80%,rgba(236,72,153,.25) 0,transparent 70%);
}
.grid{
  position:absolute;inset:0;
  background-image:linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);
  background-size:80px 80px;
}
.content{position:relative;z-index:1;text-align:center;max-width:1200px;padding:60px}
h1{font-size:96px;font-weight:900;line-height:1.1;letter-spacing:-.03em;margin-bottom:30px}
.accent{background:linear-gradient(135deg,#818cf8,#e879f9);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
h2{font-size:64px;font-weight:800;line-height:1.2;margin-bottom:20px;color:#e2e8f0}
p{font-size:32px;line-height:1.6;color:#94a3b8;max-width:900px;margin:0 auto}
.tag{display:inline-block;padding:8px 24px;border:1px solid rgba(129,140,248,.4);border-radius:40px;font-size:18px;letter-spacing:.15em;text-transform:uppercase;color:#a5b4fc;margin-bottom:40px}
.emoji{font-size:80px;margin-bottom:20px}
@keyframes fadeUp{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}
.anim{animation:fadeUp .8s ease-out both}
.d1{animation-delay:.2s}.d2{animation-delay:.4s}.d3{animation-delay:.6s}.d4{animation-delay:.8s}
</style>
`;

const makePage = (title, body) =>
  `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>${title}</title>${CSS}</head><body><div class="bg-grad"></div><div class="grid"></div>${body}</body></html>`;

// ── 4. 定义每帧 HTML ──
// key = graph node id
const frames = {
  scene_1: makePage('场景1', `<div class="content"><h1 class="anim d1"><span class="accent">标题</span></h1><p class="anim d2">副标题</p></div>`),
  scene_2: makePage('场景2', `<div class="content"><div class="emoji anim">📖</div><h2 class="anim d1">内容标题</h2><p class="anim d3">说明文字</p></div>`),
  // ... 更多帧
};

// ── 5. 写入帧 ──
for (const node of graph.nodes) {
  const html = frames[node.id];
  if (!html) { console.log(`  ⚠️ No HTML for ${node.id}`); continue; }
  const r = await orchestrator.writeFrameHtml(project.id, node.id, html);
  console.log(`  ✅ ${node.id} (${r.frame.durationSec}s)`);
}

// ── 6. 渲染 MP4 ──
console.log(`\n📦 ${graph.nodes.length} frames ready. Rendering...\n`);
const result = await orchestrator.exportMp4({
  projectId: project.id,
  onProgress: (pct, stage) => {
    if (Math.round(pct) % 20 === 0 || pct >= 99) {
      console.log(`  🎬 ${Math.round(pct)}% — ${stage}`);
    }
  }
});

console.log(`\n🏆 DONE! ${result.outputPath}`);
