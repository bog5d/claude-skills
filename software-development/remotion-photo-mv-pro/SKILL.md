---
name: remotion-photo-mv-pro
description: 用 Remotion 4.0 生成智能照片MV，支持鼓点同步切换（BPM量化）、照片循环复用、运镜动画。输出1080p 30fps H.264 MP4。
---

# Remotion Photo MV Pro — 智能照片MV生成

## 概览

核心问题与解法：
1. **照片数量远少于音乐时长** → 照片循环复用，不是拉长每张停留时间
2. **切换与音乐脱节** → BPM分析 + 节拍量化，每N拍切一次
3. **歌词字幕不同步** → Suno歌词时间轴估算不准，**默认不加歌词**，稳定优先
4. **运镜单调** → 每张照片用缩放动画 + 在拍点做闪切

## 触发条件

用户说"照片做MV"、"生成视频"、"remotion做相册"、"给照片配乐做视频"

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

```bash
# 1. 解码为单声道16kHz WAV
ffmpeg -y -i public/background_music.mp3 -ac 1 -ar 16000 /tmp/bpm.wav

# 2. 计算beat spectrum
python3 -c "
import numpy as np, wave
with wave.open('/tmp/bpm.wav') as wf:
    sr = wf.getframerate()
    audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(float)/32768.0
hop = 512
n = (len(audio)-hop)//hop + 1
energy = np.array([np.sum(audio[i*hop:(i+1)*hop]**2) for i in range(n)])
onset = np.maximum(np.diff(energy).astype(float), 0)
lags = range(max(1,int(60*n/(sr/hop))), min(len(onset),int(200*n/(sr/hop))))
scores = [(int(np.sum(onset[:-l]*onset[l:])), l) for l in lags]
best_score, best_lag = max(scores)
bpm = (sr/hop) * 60 / best_lag
print(f'BPM: {bpm:.1f} (lag={best_lag})')
top5 = sorted(scores, reverse=True)[:5]
for s, l in top5:
    print(f'  {(sr/hop)*60/l:.1f} BPM (score={s})')
"
```

**方法2：快速假设（Suno歌曲）**

Suno AI生成的歌曲BPM通常稳定在120左右。如果确认音乐来自Suno，可直接用 `BPM=120, BEAT_INTERVAL=15帧`，跳过分析。

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

### Phase 2: 节奏与切换调度计算

**核心公式：**

```
总帧数 = 音乐时长(秒) × 30fps
BEAT_INTERVAL = 15 帧  (0.5秒, BPM=120时的1拍)
SWITCH_INTERVAL = 2    (每2拍切换一次照片 = 1秒)
SWITCH_FRAMES = BEAT_INTERVAL × SWITCH_INTERVAL = 30 帧

照片索引 = Math.floor(当前帧 / SWITCH_FRAMES) % 照片总数
```

**关键决策：照片应该循环，而不是平均分配时长**

当音乐长度(258秒)远大于照片能合理展示的时间时(44张×2秒=88秒)：
- ❌ 不要 `durationPerPhoto = 总帧数 / 照片数`（每张近6秒，太慢）
- ✅ 用循环：`照片索引 = (帧 / SWITCH_FRAMES) % 照片数`，每张1秒，循环约6轮

**切换节奏可选方案：**
| 方案 | 每几张Beat切 | 每张时长 | 总切换次数 | 每张出现次数(44张) |
|------|-------------|---------|-----------|-----------------|
| 紧凑 | 1 beat | 0.5s | 516次 | ~11次 |
| 推荐 | **2 beats** | **1s** | **258次** | **~6次** |
| 缓和 | 4 beats | 2s | 129次 | ~3次 |

**Suno歌曲结构参考（BPM=120时）：**
- Intro: 0-8拍 (4秒)
- Verse: 8-72拍 (32秒)
- Pre-Chorus: 72-104拍 (16秒)
- Chorus: 104-152拍 (24秒)
- (重复结构)
- Bridge: 较缓和
- Outro: 渐慢

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

#### PhotoMV.tsx 核心实现

```tsx
import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
  Audio,
  interpolate,
} from "remotion";

// 照片列表（已排序）
const PHOTO_FILES = [...]; // 从 ls 结果生成
const PHOTO_URLS = PHOTO_FILES.map((f) => staticFile(`zt_pic/${f}`));
const PHOTO_COUNT = PHOTO_FILES.length;

// 节奏参数（BPM=120）
const BEAT_INTERVAL = 15;           // 每拍15帧@30fps
const PHOTO_SWITCH_INTERVAL = 2;    // 每2拍切一次
const SWITCH_FRAMES = 30;           // 每张照片持续30帧=1秒
const TRANSITION_FRAMES = 6;        // 转场过渡6帧≈0.2秒

export const PhotoMV: React.FC = () => {
  const frame = useCurrentFrame();

  // 循环照片索引
  const beatCycle = Math.floor(frame / SWITCH_FRAMES);
  const currentPhotoIndex = beatCycle % PHOTO_COUNT;
  const frameInBeat = frame % SWITCH_FRAMES;

  // 转场动画：快速pop效果
  let opacity: number;
  let scale: number;

  if (frameInBeat < TRANSITION_FRAMES) {
    const t = frameInBeat / TRANSITION_FRAMES;
    opacity = interpolate(t, [0, 0.3, 1], [0.3, 0.6, 1]);
    scale = interpolate(t, [0, 0.5, 1], [1.12, 0.98, 1]);
  } else {
    const steadyProgress = (frameInBeat - TRANSITION_FRAMES) /
      (SWITCH_FRAMES - TRANSITION_FRAMES);
    opacity = 1;
    scale = interpolate(steadyProgress, [0, 1], [1, 1.03]);
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* @ts-ignore */}
      <Audio src={staticFile("background_music.mp3")} volume={0.85} />

      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <img
          src={PHOTO_URLS[currentPhotoIndex]}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            opacity,
            transform: `scale(${scale})`,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
```

**转场动画说明：**
- 每张照片显示30帧（1秒），刚好2个拍子
- 前6帧为转场期：快速pop效果（scale 1.12→0.98→1, opacity 0.3→1）
- 后24帧为稳定期：缓慢推近（scale 1→1.03）
- 转场在拍点上完成

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

# TypeScript校验
npx tsc --noEmit

# 渲染
npx remotion render src/index.ts PhotoMV out_beat.mp4 --codec h264

# 压缩（Telegram友好）
ffmpeg -i out_beat.mp4 -c:v libx264 -preset fast -crf 32 -c:a aac -b:a 64k -vf "scale=854:480" -movflags +faststart out_small.mp4 -y
```

### Phase 5: 交付

- 原始文件 >50MB时，用ffmpeg压缩到~7MB（480p, CRF32）
- 通过 MEDIA: 协议发送到Telegram
- 如果MEDIA发送失败（大文件超时），先用 `-crf 32 -vf "scale=854:480"` 压缩到<10MB再发

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

## 视频+照片混合MV（进阶）

如果用户同时有视频片段和照片：
1. 视频片段用 `ffmpeg -ss START -t DUR -i video.mp4` 截取精华段落（每段3-8秒）
2. 截取的视频片段放到 `public/clips/` 目录下
3. 在代码中混排：视频用 `<Video src={staticFile("clips/clip1.mp4")} />`
4. 照片和视频交替出现，节奏统一按BPM切换

## 参考实现

现有参考项目：`~/aider_workspace/photo_mv/`
核心文件：`src/PhotoMV.tsx`, `src/Root.tsx`
