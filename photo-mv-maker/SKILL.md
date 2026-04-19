---
name: photo-mv-maker
description: Use when creating a music video (MV) from photos, videos, and music sourced from a 123pan share link. Covers downloading assets, cleaning AI-generated audio announcements, transcribing lyrics, semantic image-text matching with Claude Vision, and rendering with Remotion.
---

# photo-mv-maker

## Overview
丢一个123网盘分享链接，自动产出竖屏MV视频（MP4）。
技术栈：Python pipeline + Remotion/React + Claude Vision API

## 快速开始

```bash
# 1. 下载素材
python mv_pipeline/pan_downloader.py "https://www.123684.com/s/XXXX" "密码" mv_pipeline/assets/

# 2. 清洗音频（截掉AI声明片段）
python mv_pipeline/audio_cleaner.py assets/audio/歌曲.mp3

# 3. 转录歌词时间戳
python mv_pipeline/transcriber.py assets/audio/歌曲_clean.mp3 assets/timestamps.json

# 4. 语义图文匹配（生成/更新 script.json）
python mv_pipeline/script_matcher.py assets/script.json

# 5. 渲染 MV
cd dafeifei-mv && npx remotion render src/index.ts DaFeiFeIMV out/mv.mp4
```

## 各模块职责

| 脚本 | 输入 | 输出 |
|------|------|------|
| `pan_downloader.py` | 分享URL + 密码 | `assets/{audio,image,video}/` + `manifest.json` |
| `audio_cleaner.py` | `.mp3` | `_clean.mp3` + `.report.json` |
| `transcriber.py` | `_clean.mp3` | `timestamps.json`（带时间戳歌词段） |
| `script_matcher.py` | `script.json` + `timestamps.json` + 图片 | 更新后的 `script.json` |
| `MV.tsx` | `script.json` + 素材 | Remotion 组件 → MP4 |

## script.json 结构

```json
{
  "title": "歌曲名",
  "audio": "assets/audio/xxx_clean.mp3",
  "duration": 214,
  "fps": 25,
  "width": 1080, "height": 1920,
  "segments": [
    { "id": 0, "type": "title", "start": 0, "end": 8, "text": "...", "subtext": "..." },
    { "id": 1, "type": "photo", "file": "assets/image/xxx.jpg",
      "start": 6, "end": 24, "text": "歌词文字",
      "kb": { "fromScale": 1.0, "toScale": 1.1, "fromX": 0, "toX": -20, "fromY": 0, "toY": 0 } },
    { "id": 6, "type": "video", "file": "assets/video/xxx.mp4",
      "start": 94, "end": 124, "videoStart": 0, "videoEnd": 30, "text": "..." }
  ]
}
```

## Remotion 关键注意事项

- **视频片段用 `<OffthreadVideo>`**，不要用 `<Video>`。`<Video>` 依赖浏览器 seek，会乱帧；`<OffthreadVideo>` 用 ffmpeg 逐帧提取，帧精准。
- `startFrom` 单位是**视频帧数**（= `videoStart秒 × fps`），不是秒。
- `<Sequence from={...}>` 内 `useCurrentFrame()` 从0开始，KenBurns/SlideText 动画正确。
- 片段间交叉淡入淡出：相邻片段时间重叠2s（FADE=18帧@25fps），两个 Sequence 同时渲染，依赖 opacity 插值。

## audio_cleaner 关键词覆盖

当前检测覆盖：
- `"当前内容由ai生成"` 及所有变体
- Suno/Udio/Boomy 等平台名称
- 支持 Whisper 转录误差的**滑动窗口模糊匹配**（阈值 0.72）
- 若未检测到声明则原文件直接复制，report.json 记录结果

如需新增关键词，编辑 `audio_cleaner.py` 顶部 `AI_KEYWORDS` 列表。

## 常见问题

| 问题 | 原因 | 修复 |
|------|------|------|
| 视频片段乱帧 | 用了 `<Video>` | 改为 `<OffthreadVideo>` |
| AI声明未截断 | 关键词不全或Whisper乱码 | 扩充 `AI_KEYWORDS` 或降低 `FUZZY_THRESHOLD` |
| 图片配文不贴切 | 纯时间对齐，无语义 | 运行 `script_matcher.py`（需 `ANTHROPIC_API_KEY`） |
| 歌词乱码严重 | Whisper `base` 模型精度 | 改用 `medium`/`large` 模型（`transcriber.py` 第15行） |
| 123pan下载失败 | 视频URL需单独获取 | `pan_downloader.py` 已处理 Category==2 的特殊逻辑 |

## 环境依赖

```bash
pip install openai-whisper ffmpeg-python anthropic
# ffmpeg 需在 PATH 中
npm install  # 在 dafeifei-mv/ 目录
```
