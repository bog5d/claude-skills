---
name: ai-qujing-video
description: 用 AI 取经记管线将 HTML 幻灯片转为视频。支持从 config.json 驱动场景，通过 TTS → Jinja2 渲染 → Playwright 截图 → ffmpeg 合片产出 MP4。
---

# AI 取经记 — HTML 幻灯片视频管线

## 触发条件
- 用户说"做AI取经记"、"文字转视频"、"html转视频"、"ai qujing"
- 做知识漫画/文章转视频时

## 管线架构

```
config.json → TTS (edge_tts) → Jinja2 渲染 → Playwright 截图 → ffmpeg 合片 → MP4
```

## 目录结构

```
~/.hermes/tools/ai-qujing/
├── config.json          ← 改这里出新集
├── templates/slide.html ← Jinja2 模板（CSS 不混 Python）
├── build.py             ← 编排器
├── renderer.py          ← 渲染引擎
├── encoder.py           ← 编码器
└── tts.py               ← 语音合成
```

## 产出新一集

```bash
cd ~/.hermes/tools/ai-qujing
cp config.json episode-03.json   # 改 scenes 内容
python build.py --config episode-03.json --out output/ep03
```

## config.json 结构

```json
{
  "episode": "03",
  "title": "AI 取经记 03 — xxx",
  "watermark": "AI 取经记 03",
  "voice": "zh-CN-YunxiNeural",
  "video": { "width": 1080, "height": 1920, "fps": 30, "padding_seconds": 2.5 },
  "scenes": [
    {
      "id": "01",
      "text": "旁白文本（给 TTS 念的）",
      "bg": "linear-gradient(...)",
      "big": "大标题",
      "sub": "副标题",
      "big_color": "#ffd700",
      "big_size": 64,
      "sub_size": 36,
      "sub_color": "#ccc",
      "big_top": 500,
      "sub_margin": 80
    }
  ]
}
```

## 坑和教训

1. **CSS 和 Python 模板分离** — 旧版 `.format()` 吃 CSS 花括号，Jinja2 `{{ }}` 天然隔离，不用转义
2. **Playwright 用 Python API 不用 CLI** — `npx playwright screenshot` 对本地 HTML 不稳定，`sync_playwright()` 稳定
3. **ffmpeg concat 用绝对路径** — `-f concat` 相对路径相对于 concat 列表文件位置，不是 cwd
4. **Playwright 装包 ≠ 装浏览器** — `pip install playwright` 后必须 `playwright install chromium`
5. **图片不强用** — 文章中的图是备选，不符合场景的跳过，纯 CSS 渐变也够用

## 依赖

- Python: `jinja2`, `playwright`, `edge_tts`, `Pillow`
- 系统: `ffmpeg`, `ffprobe`
- Playwright: `chromium` 浏览器（`playwright install chromium`）
