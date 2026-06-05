---
name: ai-qujing-video
description: 用 AI 取经记管线将文章转为专业视频。全链路：文章分析 → 脚本改编 → 分镜生成 → 多视觉渲染 → 字幕/BGM/转场 → MP4。输出观众可交付级别视频。
---

# AI 取经记 — 完整视频生产管线 v2

## 触发条件
- 用户说"做AI取经记"、"文字转视频"、"html转视频"、"ai qujing"、"文章转视频"
- 用户批评视频质量不够交付级 → 自动升级到 v2 全链路
- 做知识漫画/文章转视频时

## ⚠️ 核心认知（必须理解）

**文章 ≠ 视频脚本。** 这是最大的认知鸿沟。直接把文章丢给 TTS 念出来 = 不合格的视频。

专业视频制作的核心是 **Pre-Production 占 50% 时间**：
1. 先分析文章结构
2. 改写成口语化脚本（视觉锚定每句话）
3. 做分镜规划（每帧：看到什么 → 听到什么 → 情绪是什么）
4. 才进入画面生产

## v2 管线架构

```
Phase 0-2: 预生产 (preprod.py)
  config.json → 文章分析 → 脚本改编 → 分镜生成 → storyboard.json

Phase 4: TTS (tts.py)
  storyboard.json → Edge TTS → MP3 音频段

Phase 3: 视觉生产 (visual/producer.py)
  storyboard.json → 多类型画面渲染 → PNG 帧序列

Phase 5: 编码+后期 (encoder.py + postproc.py)
  PNG帧+MP3 → ffmpeg编码 → 字幕烧录 → BGM混音 → 转场 → 最终 MP4
```

## 目录结构

```
~/.hermes/tools/ai-qujing/
├── build.py               ← 编排器 (v2 全链路)
├── preprod.py             ← Phase 0-2: 文章分析+脚本+分镜
├── tts.py                 ← Phase 4: TTS 语音合成
├── encoder.py             ← Phase 5: ffmpeg 编码+合片
├── postproc.py            ← Phase 5: 字幕/BGM/转场
├── visual/
│   ├── __init__.py
│   └── producer.py        ← Phase 3: 6 种视觉类型渲染器
├── config.json            ← 场景数据（改这里出新集）
└── templates/slide.html   ← Jinja2 模板 (v1 遗留, v2 用 PIL 直绘)
```

## 产出新一集

```bash
cd ~/.hermes/tools/ai-qujing
cp config.json episode-03.json   # 改 scenes 内容
python build.py --config episode-03.json --out output/ep03
# 可选: 加 BGM
python build.py --config episode-03.json --bgm ~/Music/bgm.mp3
```

## 六种视觉类型

| 类型 | 适用场景 | 效果 |
|------|----------|------|
| `gradient_text` | 通用场景 | 渐变背景+文字+Ken Burns 微动 |
| `cinematic_text` | 开篇/结尾/高潮 | 暗色+暗角+光晕+粒子+文字推入 |
| `tech_abstract` | 技术概念 | 暗色网格+扫描线+数据节点 |
| `motion_infographic` | 数据/流程图 | 动态线框+脉动节点 |
| `ai_concept_art` | 抽象概念（如唐僧） | 暗色调+纹理+光晕（后期可替换AI生图） |
| `corporate_visual` | 金融/商务 | 暗蓝+金色几何线+数据点 |

分镜生成器（preprod.py）会根据场景内容**自动推断**合适的 visual_type。

## 分镜生成规则 (preprod.py)

关键词匹配自动分派 visual_type:
- "代码/函数/API/架构" → `motion_infographic`
- "唐僧/孙悟空/妖怪/西游" → `ai_concept_art`
- "AI/模型/智能/Agent/Tool" → `tech_abstract`
- "融资/资本/尽调/机构" → `corporate_visual`
- "幻灭/诞生/壁垒/开始" → `cinematic_text`
- 其他 → `gradient_text`

情绪推断: epic_uplifting / dramatic_tense / hopeful_future / analytical_focused / powerful_confident / inspirational_flow

## config.json 结构 (v2)

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
      "bg": "linear-gradient(135deg, #1a0a2e 0%, #16213e 50%, #0f3460 100%)",
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

## 已知坑（5个核心教训）

1. **CSS 和 Python 模板必须分离** — `.format()` 吃 CSS 花括号，`Jinja2 {{ }}` 天然隔离。v2 改用 PIL 直绘，彻底绕开。
2. **Playwright 用 Python API 不用 CLI** — `npx playwright screenshot` 对本地 HTML 不稳定（`[RTK:PASSTHROUGH]` 解析全败），`sync_playwright()` 稳定。
3. **ffmpeg concat 必须用绝对路径** — `-f concat` 相对路径相对于 concat 列表文件位置，不是 cwd。用 `path.resolve()`。
4. **Playwright 装包 ≠ 装浏览器** — `pip install playwright` 后必须 `playwright install chromium`。
5. **图片不强用** — 文章中的图是备选，不符合场景的跳过。v2 的 6 种视觉类型覆盖了所有场景。

## 字幕生成

postproc.py 从分镜数据自动生成 SRT 字幕：
- 按 narration 句号自动拆分台词
- 烧录到视频（尝试硬件加速 h264_videotoolbox → 回退 libx264）
- 字体: STHeiti Medium, 28px, 白字黑边

## BGM

- `--bgm path/to/bgm.mp3` 参数指定
- 默认音量 12%（`bgm_volume=0.12`）
- BGM 自动循环到视频长度

## 转场

- postproc.py 支持片段间交叉淡化（crossfade 0.5s）
- ffmpeg filter_complex: xfade + acrossfade

## 依赖

- Python: `jinja2`, `playwright`, `edge_tts`, `Pillow`
- 系统: `ffmpeg`, `ffprobe`
- Playwright: `chromium` 浏览器（`playwright install chromium`）
- 字体: `/System/Library/Fonts/STHeiti Medium.ttc` (macOS)
