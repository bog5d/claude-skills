---
name: photo-mv-maker
description: Use when creating a music video (MV) from photos, videos, and music. Input can be a 123pan share link OR a local directory path. Covers asset ingestion, AI audio cleaning, Qwen3-ASR song transcription, Claude lyric correction, beat-synced timing, SigLIP+Claude semantic image-text matching, Claude Vision director ordering, and Remotion rendering.
---

# photo-mv-maker

## Overview
一条命令链从素材到成片的竖屏 MV pipeline（1080×1920）。
输入支持：123pan 分享链接 **或** 本地目录。
技术栈：Python + Qwen3-ASR + SigLIP 2 + Claude Vision + librosa + Remotion

---

## 完整流程（7步）

```bash
# 0. 环境变量
export ANTHROPIC_API_KEY=sk-ant-...

# 1. 下载/导入素材（自动识别链接或本地路径）
python mv_pipeline/ingest.py "https://www.123684.com/s/XXXX" --pwd 密码
# 或
python mv_pipeline/ingest.py /本地/照片目录/

# 2. 清洗音频（截掉 AI 声明片段）
python mv_pipeline/audio_cleaner.py assets/audio/歌曲.mp3

# 3. 歌词转录：Qwen3-ASR（首选）→ Whisper 回退 → Claude 纠错
python mv_pipeline/transcriber.py assets/audio/歌曲_clean.mp3

# 4. 节拍对齐（librosa 检测鼓点，切片时机自动踩点）
python mv_pipeline/beat_aligner.py assets/script.json assets/audio/歌曲_clean.mp3

# 5. 语义图文匹配（SigLIP 粗排 + Claude Vision 精选）
python mv_pipeline/script_matcher.py assets/script.json

# 6. 导演排序（Claude Vision 情感弧线重排照片顺序）
python mv_pipeline/director.py assets/script.json --arc rise-peak-fall

# 7. 渲染 MV
cd dafeifei-mv && npx remotion render src/index.ts DaFeiFeIMV out/mv.mp4
```

---

## 各模块速查

| 脚本 | 核心能力 | 主要依赖 |
|------|---------|---------|
| `ingest.py` | 链接/本地双入口，生成 manifest.json | 无额外依赖 |
| `audio_cleaner.py` | Whisper + 模糊关键词检测 AI 声明片段 | whisper, ffmpeg |
| `transcriber.py` | Qwen3-ASR（歌曲专属）→ Whisper 回退 → Claude 纠错 | transformers, whisper, anthropic |
| `beat_aligner.py` | librosa 节拍检测，切点吸附到鼓点 | librosa |
| `script_matcher.py` | SigLIP 2 本地粗排 + Claude Vision 精选 | transformers, anthropic |
| `director.py` | Claude Vision 批量分析情感 → 弧线排序 | anthropic |
| `MV.tsx` | Remotion 渲染，使用 OffthreadVideo（帧精准）| remotion |

---

## script.json 结构

```json
{
  "title": "歌曲名",
  "audio": "assets/audio/xxx_clean.mp3",
  "duration": 214, "fps": 25,
  "width": 1080, "height": 1920,
  "segments": [
    { "id": 0, "type": "title", "start": 0, "end": 8,
      "text": "大标题", "subtext": "副标题" },
    { "id": 1, "type": "photo", "file": "assets/image/xxx.jpg",
      "start": 6, "end": 24, "text": "歌词文字",
      "kb": { "fromScale":1.0,"toScale":1.1,"fromX":0,"toX":-20,"fromY":0,"toY":0 } },
    { "id": 6, "type": "video", "file": "assets/video/xxx.mp4",
      "start": 94, "end": 124, "videoStart": 0, "videoEnd": 30, "text": "..." }
  ]
}
```

---

## 关键技术决策

### 歌词转录：Qwen3-ASR > Whisper
- Qwen3-ASR 专为 speech/music/song 调优，中文 WER ~1.2（vs Whisper base ~4.7）
- 自动回退：Qwen3-ASR 失败 → Whisper large-v2
- Claude 纠错：ASR 结果交 Claude 做上下文推理，修正残余错别字
- 若有准确歌词来源（歌词网站），可跳过 ASR，直接用 WhisperX forced alignment 对时间戳

### 图文匹配：两级策略
- Stage 1：SigLIP 2 本地运行（google/siglip-so400m-patch14-384），免 API 费用，筛 Top-3
- Stage 2：Claude claude-sonnet-4-6 Vision 精选，API 调用次数 = 片段数（不是片段×歌词数）

### 节拍对齐：librosa
- `librosa.beat.beat_track()` 检测所有鼓点时间
- 片段边界吸附到 ±1.5s 内的最近鼓点
- 保留 2s 交叉淡入淡出重叠（对应 MV.tsx `FADE=18` 帧 @25fps）

### 视频渲染：OffthreadVideo
- 用 `<OffthreadVideo>` 不用 `<Video>`，ffmpeg 逐帧提取，帧精准无乱帧
- `startFrom` 单位是**视频帧数**（= videoStart秒 × fps）

### 导演排序：情感弧线
- 可选模式：`rise-peak-fall`（默认）/ `journey` / `nostalgia` / `custom`
- 一次批量 Claude 调用分析所有照片情感，再一次调用排序
- 排序只改 file/text/kb，不改 start/end（时间轴由 beat_aligner 固定）

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| Qwen3-ASR 下载慢 | 模型 ~2GB | 用 `--model whisper` 跳过；或提前 `huggingface-cli download Qwen/Qwen3-ASR-2B` |
| SigLIP 加载报错 | transformers 版本 | `pip install -U transformers` |
| 导演排序结果不理想 | 弧线描述太宽泛 | 用 `--arc custom --arc-desc "开头轻松玩耍，中间温馨团聚，结尾离别思念"` |
| 节拍对齐时长太短 | 歌曲 BPM 高，MIN_DUR 限制 | 调整 `beat_aligner.py` 的 `MIN_DUR` 参数 |
| 视频片段乱帧 | 用了 `<Video>` | 改为 `<OffthreadVideo>`（已修复） |
| AI 声明未截断 | Whisper 转录误差大 | 降低 `audio_cleaner.py` 的 `FUZZY_THRESHOLD`（默认 0.72） |

---

## 环境依赖

```bash
# Python
pip install anthropic transformers torch accelerate pillow
pip install openai-whisper librosa soundfile
# ffmpeg 需在 PATH 中（用于音频处理和视频渲染）

# Node.js（Remotion 渲染）
cd dafeifei-mv && npm install
```

## 可借鉴的开源参考

- [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) — 歌曲级 ASR，强烈推荐替换 Whisper base
- [OpenMontage](https://github.com/calesthio/OpenMontage) — 同类 Python+Remotion 全流程 pipeline，架构参考
- [WhisperX](https://github.com/m-bain/whisperX) — 有准确歌词时做 forced alignment（对齐时间戳）
- [SigLIP 2](https://huggingface.co/google/siglip-so400m-patch14-384) — 本地多模态图文匹配
