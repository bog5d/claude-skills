---
name: remotion-photo-mv-pro
description: 用 Remotion 4.0 生成智能照片MV，支持鼓点同步切换（BPM量化）、照片循环复用、运镜动画。输出1080p 30fps H.264 MP4。
---

# Remotion Photo MV Pro — 智能照片MV生成

## 硬路由（必须遵守）

照片 MV 必须优先调用程序化流水线，禁止让模型临场手写 Remotion 项目、手写图片路径、手写渲染命令。

唯一默认入口：

```bash
python3 /Users/mac/.hermes/profiles/her-m2/tools/mv_pipeline/mv_pipeline.py run \
  --project /Users/mac/.hermes/profiles/her-m2/home/aider_workspace/photo_mv_gushan \
  --photos /path/to/photos \
  --music /path/to/background_music.mp3 \
  --theme family_warm \
  --title "标题" \
  --compress \
  --send
```

分步调试入口：

```bash
python3 /Users/mac/.hermes/profiles/her-m2/tools/mv_pipeline/mv_pipeline.py build \
  --project /Users/mac/.hermes/profiles/her-m2/home/aider_workspace/photo_mv_gushan \
  --photos /path/to/photos \
  --music /path/to/background_music.mp3 \
  --theme family_warm \
  --title "标题"

python3 /Users/mac/.hermes/profiles/her-m2/tools/mv_pipeline/mv_pipeline.py render \
  --project /Users/mac/.hermes/profiles/her-m2/home/aider_workspace/photo_mv_gushan \
  --output /Users/mac/.hermes/profiles/her-m2/home/aider_workspace/photo_mv_gushan/output_remotion.mp4

python3 /Users/mac/.hermes/profiles/her-m2/tools/mv_pipeline/mv_pipeline.py qc \
  --video /Users/mac/.hermes/profiles/her-m2/home/aider_workspace/photo_mv_gushan/output_remotion.mp4

python3 /Users/mac/.hermes/profiles/her-m2/tools/mv_pipeline/mv_pipeline.py send \
  --video /Users/mac/.hermes/profiles/her-m2/home/aider_workspace/photo_mv_gushan/output_remotion_telegram.mp4
```

如果素材已经在项目 `public/` 下，`build` 可以省略 `--photos` 和 `--music`，但仍必须运行 `build` 来重建标准模板和 `mv_config.json`。

发送规则：
- `run --send` 是默认交付方式，内部会先 `build/render/qc/compress/qc`，全部通过才发送。
- 独立 `send` 命令也会先运行 QC，`passed: true` 才发送视频。
- `qc` 失败时禁止发送，必须把失败原因报告给用户。
- 黑屏、破图、视频码率过低、音频缺失、时长异常，都视为失败。

模型只允许介入：
- 选择主题：`family_warm` / `travel_beat` / `fast_pop`
- 写标题或短字幕
- 解释 QC 报告

模型不允许介入：
- 手写 `<img src=...>` 图片路径
- 绕过 `staticFile()`
- 绕过 `public/` 素材目录
- 跳过 `qc`
- 文件存在就宣称完成

## 概览

核心问题与解法（v2 升级）：
1. **照片数量远少于音乐时长** → 照片循环复用，不是拉长每张停留时间
2. **切换与音乐脱节** → **v2 升级：真实 Onset 检测**，五步管道（BPM→峰值→合并→补拍→采样），每个切换点对应实际音乐节拍
3. **切换间隔可变** → Chorus 高潮密集切片，Verse 稀疏切片，完全跟随音乐强弱起伏
4. **运镜单调** → 每张照片用缩放动画（Ken Burns）+平移，fade 时长按真实节拍间隔自适应
5. **歌词字幕不同步** → Suno歌词时间轴估算不准，**默认不加歌词**，稳定优先

## 触发条件

用户说"照片做MV"、"生成视频"、"remotion做相册"、"给照片配乐做视频"

## 主题 ↔ 节拍映射

主题现在用 `beats_per_switch`（每个切换跨几个节拍），由 `detect_onsets()` 自动分析真实节拍后采样。

| 主题 | beats_per_switch | 典型间隔 | 适用场景 |
|------|:---:|:---:|------|
| `fast_pop` | 2 | ~0.8-0.9s（@134BPM） | 快节奏、生日/派对、BPM≥120 |
| `travel_beat` | 3 | ~1.3s | 旅行、中等节奏 |
| `family_warm` | 6 | ~3.5s | 慢节奏、温馨回顾 |

**不再是固定间隔！** `detect_onsets()` 对音频做真实节拍检测，每个切换点的帧号都是实际的音乐节拍位置。Chorus 高潮段切换密集，Verse 段落切换稀疏——完全跟音乐走。

**规则**：BPM ≥ 120 → 选 `fast_pop`；BPM 60-120 → 选 `travel_beat`；BPM < 60 → 选 `family_warm`。

## 照片数量规划

```
每张出现次数 = 总帧数 / (照片数 × switch_frames)
理想区间: 5-15 次/张（太少=单调，太多=眼花）
```

| 歌曲时长 | 推荐最少照片数 (fast_pop) | 每张出现约 |
|---------|:---:|:---:|
| 2分钟 | 12张 | 10次 |
| 4分钟 | 24张 | 10次 |
| 6分钟 | 36张 | 10次 |

实际案例：238秒 + 29张 + fast_pop → 7138/(29×30) ≈ 8次/张 ✅

## 工作流

### Phase 0: 音乐源获取

#### 检查已有音乐文件
```bash
ls -la ~/aider_workspace/photo_mv/public/*.mp3 ~/aider_workspace/photo_mv/public/*.wav 2>/dev/null
```

#### 123云盘下载（仅限以下方案）
**只有方案C稳定可靠。A/B已验证失败多次，不要浪费时间重试。**

✅ **方案C（推荐）：用户直接通过Telegram发文件**
用户发来文件后：
- MP3 → 复制到 `public/background_music.mp3`
- 自动 `ffprobe` 获取时长、BPM信息

❌ ~~方案A（浏览器拦截）：123云盘反爬太强，download URL有签名校验~~
❌ ~~方案B（Python requests）：需要完整cookie + token链，经常返回code=-3~~

#### BPM分析

**方法1：Beat Spectrum法（推荐，鲁棒性强）**

⚠️ 长音频（>2分钟）必须先截取前60秒再做BPM分析，否则 `min_lag > max_lag` 导致 range 为空、`max()` 报错。

```bash
# 1. 截取前60秒并解码为单声道16kHz WAV
ffmpeg -y -i public/background_music.mp3 -ac 1 -ar 16000 -t 60 /tmp/bpm_60s.wav

# 2. 计算beat spectrum（修正版：确保 min_lag ≤ max_lag）
python3 -c "
import numpy as np, wave
with wave.open('/tmp/bpm_60s.wav') as wf:
    sr = wf.getframerate()
    audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(float)/32768.0
hop = 512
n = (len(audio)-hop)//hop + 1
bpm_fr = sr / hop
energy = np.array([np.sum(audio[i*hop:(i+1)*hop]**2) for i in range(n)])
onset = np.maximum(np.diff(energy).astype(float), 0)
# 修正：用BPM边界(60~200)反算lag范围，避免空range
min_lag = max(1, int(60 * bpm_fr / 200))   # 200 BPM → min lag
max_lag = min(len(onset)-1, int(60 * bpm_fr / 60))  # 60 BPM → max lag
lags = list(range(min_lag, max_lag+1))
scores = [(int(np.sum(onset[:-l]*onset[l:])), l) for l in lags]
best_score, best_lag = max(scores)
bpm = bpm_fr * 60 / best_lag
print(f'BPM: {bpm:.1f} (lag={best_lag}, score={best_score})')
top5 = sorted(scores, reverse=True)[:5]
for s, l in top5:
    print(f'  {bpm_fr*60/l:.1f} BPM (score={s})')
"
```

**方法2：快速假设（Suno歌曲）**

Suno AI 生成的歌曲 BPM 通常在 120-140 区间。如果确认来源为 Suno 且无法立即分析，可用 `BPM=130` 作为临时默认，但仍强烈建议跑方法1确认。实际案例：Suno 生日歌《大飞飞吹蜡烛》实测 BPM=134。

**参数映射（得到BPM后）：**
```
BEAT_INTERVAL = 30 * 60 / BPM  （帧数，@30fps）
SWITCH_FRAMES = BEAT_INTERVAL × 2  （每2拍切换一次照片）
```

例：BPM=127 → BEAT_INTERVAL=14帧 → SWITCH_FRAMES=28帧
例：BPM=120 → BEAT_INTERVAL=15帧 → SWITCH_FRAMES=30帧

### Phase 1: 照片资源准备

```bash
ls -1 photos/zt_pic/*.jpg | wc -l  # 照片数量
```

照片按文件名排序（`IMG_YYYYMMDD_HHMMSS.jpg` 天然按时间排序）。

### Phase 2: Onset 检测与节拍调度

**核心变化（v2）：不再使用固定间隔。** 流水线调用 `detect_onsets()` 五步管道：

```
detect_onsets(music_file, beats_per_switch=2):
  ① BPM 检测 — beat spectrum 自相关（前60秒）
  ② Onset 峰值拾取 — 能量差分 + 85th percentile 阈值
  ③ 近邻合并 — 间距 < beat_interval/2 的合并
  ④ 长间隙补拍 — 间距 > 2.5×beat_interval 处插入合成节拍
  ⑤ 节拍采样 — 按 beats_per_switch 间隔采样
  → 返回 beat_frames: [19, 48, 69, 85, ...]（帧号）
```

**输出写入 `mv_config.json`**：
```json
{
  "beats_per_switch": 2,
  "beat_frames": [19, 48, 69, 85, 111, 129, ...],
  "transition_frames": 6
}
```

**照片仍然循环**：
```
照片索引 = beatIdx % 照片数
每张出现次数 ≈ beat_frames.length / 照片数
```

实际案例：238秒 + BPM=134 + fast_pop(每2拍) → 274个切换点 + 29张照片 → 每张约9次 ✅

### Phase 3: 项目生成

#### 目录结构
```
photo_mv/
├── src/
│   ├── index.ts          # registerRoot(Root)
│   ├── Root.tsx          # Composition
│   └── PhotoMV.tsx       # 主渲染组件（核心）
├── public/
│   ├── zt_pic/           # 照片文件
│   └── background_music.mp3  # 用户提供的背景音乐
├── remotion.config.ts
├── tsconfig.json
└── package.json
```

#### PhotoMV.tsx 核心实现（v2 节拍驱动）

```tsx
import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";

const PHOTO_FILES = ["zt_pic/01.jpg", ...];  // pipeline 生成
const BEAT_FRAMES: number[] = [19, 48, 69, ...];  // 真实节拍帧号
const BEAT_ESTIMATE = 23;  // 平均间隔，用于最后一个节拍之后的回退
const TRANSITION_FRAMES = 6;

// 二分查找：找到 ≤ frame 的最大节拍索引
function findBeatIndex(frame: number): number {
  let lo = 0, hi = BEAT_FRAMES.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >>> 1;
    if (BEAT_FRAMES[mid] <= frame) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

export const PhotoMV: React.FC = () => {
  const frame = useCurrentFrame();
  const beatIdx = findBeatIndex(frame);
  const photoIndex = beatIdx % PHOTO_FILES.length;

  const lastSwitch = BEAT_FRAMES[beatIdx];
  const nextSwitch = beatIdx + 1 < BEAT_FRAMES.length
    ? BEAT_FRAMES[beatIdx + 1]
    : lastSwitch + BEAT_ESTIMATE;
  const beatDuration = nextSwitch - lastSwitch;  // 动态！不是固定值
  const frameSinceSwitch = frame - lastSwitch;
  const progress = beatDuration > 0 ? frameSinceSwitch / beatDuration : 0;

  const fadeIn = interpolate(frameSinceSwitch, [0, TRANSITION_FRAMES], [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fadeOut = interpolate(frameSinceSwitch,
    [beatDuration - TRANSITION_FRAMES, beatDuration], [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const opacity = Math.min(fadeIn, fadeOut);
  const scale = interpolate(progress, [0, 1], [1.02, 1.09]);
  const pan = interpolate(progress, [0, 1], [-1.5, 1.5]);

  return (
    <AbsoluteFill style={{ backgroundColor: "#050505", overflow: "hidden" }}>
      {/* @ts-ignore */}
      <Audio src={staticFile("background_music.mp3")} volume={0.88} />
      <AbsoluteFill>
        <img src={staticFile(PHOTO_FILES[photoIndex])} style={{
          width: "100%", height: "100%", objectFit: "cover",
          opacity,
          transform: `scale(${scale}) translateX(${pan}%)`,
        }} />
      </AbsoluteFill>
      <div style={{
        position: "absolute", left: 36, bottom: 30,
        padding: "10px 14px", borderRadius: 6,
        background: "rgba(0,0,0,0.38)", color: "rgba(255,255,255,0.88)",
        fontSize: 24
      }}>{CAPTION}</div>
    </AbsoluteFill>
  );
};
```

**关键区别 vs v1：**
- ❌ v1: `Math.floor(frame / SWITCH_FRAMES)` — 固定间隔
- ✅ v2: `findBeatIndex(frame)` — 每帧二分查找当前节拍位置
- ❌ v1: `SWITCH_FRAMES = 30` 全局常量
- ✅ v2: `beatDuration` 每段动态计算（11~52帧不等）
- fade 动画根据真实节拍间隔自适应（短节拍快切、长节拍慢切）

#### Root.tsx
```tsx
import { Composition } from "remotion";
import { PhotoMV } from "./PhotoMV";

const FPS = 30;
const MUSIC_DURATION = 258; // 从ffprobe获取
const TOTAL_FRAMES = MUSIC_DURATION * FPS;

export const Root: React.FC = () => (
  <Composition
    id="PhotoMV"
    component={PhotoMV}
    durationInFrames={TOTAL_FRAMES}
    fps={FPS}
    width={1920}
    height={1080}
  />
);
```

### Phase 4: 渲染

```bash
cd ~/aider_workspace/photo_mv

# 首次渲染前装依赖（已有 node_modules 则跳过）
npm install --legacy-peer-deps 2>&1 | tail -3

# 渲染（后台模式，10-15分钟）
npx remotion render src/index.ts PhotoMV output_remotion.mp4 --codec h264

# 压缩（Telegram <50MB）：720p CRF28 通常能将 130MB+ 压缩到 20-25MB
ffmpeg -y -i output_remotion.mp4 \
  -c:v libx264 -preset fast -crf 28 \
  -c:a aac -b:a 96k \
  -vf "scale=1280:720" \
  -movflags +faststart \
  output_tg.mp4

# 备选：若 720p 仍 >50MB，降为 480p CRF32
ffmpeg -y -i output_remotion.mp4 \
  -c:v libx264 -preset fast -crf 32 \
  -c:a aac -b:a 64k \
  -vf "scale=854:480" \
  -movflags +faststart \
  output_tg.mp4
```

### Phase 5: 交付

- 原始文件 >50MB时，用ffmpeg压缩（720p CRF28 → 通常 20-25MB）
- 发送前复制到白名单目录：`cp output_tg.mp4 ~/.hermes/cache/documents/视频名.mp4`
- 通过 `MEDIA:/Users/mac/.hermes/cache/documents/视频名.mp4` 发送到 Telegram
- 根目录 `/tmp/` 和项目目录不在 MEDIA 白名单内，必须经过 `~/.hermes/cache/documents/` 中转
- 如果 MEDIA 发送失败（大文件超时），先用 `-crf 32 -vf "scale=854:480"` 压缩到 <10MB 再发

## 关键约束

1. **Remotion必须 pin 到 @4.0.0**（@latest 10分钟超时）
2. **手动搭脚手架** — `create-video` CLI在非TTY下挂掉
3. **用 `staticFile()` 而非 `file://`** — file://在Chrome headless下黑屏
4. **音频用 `<Audio>` 组件** — Web Audio API不会被渲染器捕获
5. **React 19 + Remotion 4.x 的 `<Audio>` 类型问题** — 加 `// @ts-ignore`
6. **Sunosong时长必须从ffprobe读取** — 不要靠猜
7. **歌词字幕默认不加** — Suno歌词时间轴是估算的，不同步。除非用户明确要求且愿意容忍误差

## Pitfalls（从实战中总结）

- **‼️ 不要用 file:// 引用图片** → 黑屏。用 `staticFile()`
- **‼️ 不要平均分配照片时长** → 当音乐(258秒) >> 照片数量(44张)，每张停留会太久(6秒)。要循环
- **‼️ 歌词时间轴估算不准** → Suno的歌词分段是纯文本标记，没有时间戳。按比例估算会偏离0.5-2秒
- **‼️ 123云盘不要去爬** → 它的下载保护有服务端签名校验，curl/requests/browser拦截全试过都失败。直接让用户发文件
- **照片没放在 `public/` 下** → `staticFile()` 只在 `public/` 目录下查找文件
- **npm install 超时** → 用 `npm install remotion@4.0.0 @remotion/cli@4.0.0 @remotion/renderer@4.0.0 --legacy-peer-deps`
- **Chrome路径问题** → 自动检测失败时加 `--chrome-binary="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`
- **MP3比WAV可靠** → Suno的MP3自带元数据，直接使用，无需转码
- **ffmpeg压缩时加 `-movflags +faststart`** → 否则视频无法流式播放，Telegram加载慢
- **渲染耗时** → 258秒(4分18秒)的MV渲染约需10-15分钟。使用 `background=true + notify_on_complete=true` 异步等待
- **QC 会误报压缩版码率** → `qc` 对 bitrate < 800kbps 标记失败。这是压缩版（Telegram用）的正常水平，原版1080p码率通常 >4000kbps。压缩版 QC 失败时可忽略，直接用原版 QC 结果判断
- **用户分批发照片** → 如果渲染已在后台跑，不要中途停掉重建。等当前渲染跑完，累积所有照片后一次性 `build + render`。项目已有 `node_modules` 时跳过 `npm install`
- **PhotoMV.tsx 的 `staticFile()` 路径** → mv_pipeline 生成代码用 `staticFile("zt_pic/01.jpg")` 而非 `staticFile(`zt_pic/${f}`)`。扩增照片后必须 `build` 重新生成，不能手动改 PHOTO_FILES 数组（pipeline 会覆写）
- **⚠️ BPM 分析用 `-t 60` 截取前60秒** → 完整长音频（>2分钟）直接做 beat spectrum 会导致 lag range 为空、`max()` 报 `ValueError`。已在 Phase 0 代码中修正
- **⚠️ Onset 阈值用百分位数** → 简单 mean+std 阈值会检出太多 sub-beat 瞬态（敲击乐、鼓点细节）。用 `np.percentile(onset_env, 85)` 只取能量 top 15% 的峰。BPM=134 时从 ~800 峰降到 ~588 有效节拍
- **⚠️ Onset 需要长间隙补拍** → Intro、Outro、Bridge 等低能量段落检测不到节拍。`gap > 2.5*beat_interval` 时插入合成节拍（均匀间隔），否则视频在这些段落会长时间停滞在同一张照片
- **⚠️ Python f-string 中生成 JSX 模板** → 双花括号 `{{` `}}` 是 Python 转义，四花括号 `{{{{` `}}}}` 是 JSX `{{` `}}`。模板字符串 `${scale}` 在 f-string 中要写成 `${{scale}}`。出错会导致 PhotoMV.tsx 出现乱码行
- **⚠️ numpy 依赖** → `detect_onsets()` 需要 numpy。确认 Python 环境可用：`python3 -c "import numpy"`。已确认 macOS 系统 Python 自带 numpy 2.0.2

## 视频+照片混合MV（进阶）

如果用户同时有视频片段和照片：
1. 视频片段用 `ffmpeg -ss START -t DUR -i video.mp4` 截取精华段落（每段3-8秒）
2. 截取的视频片段放到 `public/clips/` 目录下
3. 在代码中混排：视频用 `<Video src={staticFile("clips/clip1.mp4")} />`
4. 照片和视频交替出现，节奏统一按BPM切换

## 参考实现

现有参考项目：
- `~/aider_workspace/photo_mv/` — 44张照片 + 258秒音乐（旧版，BPM=120）
- `~/aider_workspace/photo_mv_gushan/` — 20张鼓山照片 + 190秒音乐（BPM=127）
- `~/aider_workspace/photo_mv_feifei/` — 29张生日照 + 238秒 Suno 歌（BPM=134, fast_pop）

核心文件：`src/PhotoMV.tsx`, `src/Root.tsx`, `mv_config.json`
