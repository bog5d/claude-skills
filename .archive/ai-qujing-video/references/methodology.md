# 文章转视频 — 全球顶级方法论调研（2026年6月）

## 核心发现：我们缺的不是技术，是 Pre-Production

**我们做的**: 文章原文 → TTS朗读 → 静态幻灯片 → 视频

**专业做的**: 文章 → AI提取结构/关键点/情绪弧线 → 改写为口语化视频脚本 → 逐场景分镜规划 → 匹配视觉素材 → AI视频生成 → 合成+字幕+BGM+转场+调色

## 标杆案例对比

### 1. Kapwing (Article to Video)
管线: 文章→AI提取关键点→写视频脚本→匹配视觉素材→生成草稿（配音+字幕+BGM）
- AI 自动匹配 stock 素材和 AI 生成画面到脚本的每个段落
- 所有视觉可替换（stock library / 自上传 / AI re-generate）
- 多尺寸导出（社交平台适配）
来源: https://www.kapwing.com/ai/article-to-video

### 2. VideoClaw / Synclip
管线: 粘贴剧本→AI提取角色/场景→规划剧集+分镜→AI生成分镜图→Sora/Veo渲染视频片段
- 多步骤 Agent，不离开画布
- 专为独立导演和内容工作室设计
来源: https://synclip.ai/zh-cn/blog/videoclaw-ai-storyboard-video-generator

### 3. ViMax (港大 HKUDS)
管线: 概念输入→ Director + Screenwriter + Producer + Video Generator 四 Agent 协作
- 完全自主的视频生成 Agent
- 四个角色分工，不是单管线
来源: https://github.com/HKUDS/ViMax

### 4. Framesurfer (Blog to Story Video)
核心方法论: "Stop thinking in paragraphs and start thinking in scenes."
- 故事视频需要: hook + sequence + visual movement + payoff
- 把核心想法改写为口语旁白，按场景节拍映射
- 博客是视觉视频的原材料，不是直接可用的脚本
来源: https://framesurfer.com/blogs/how-to-repurpose-a-blog-post-into-a-story-video

### 5. StudioBinder (YouTube Script Writing)
框架: Hook → Value → Call to Action
- 脚本是视频的蓝图
- 每句话都要考虑: 说出来时画面显示什么？
- 前 3 秒决定留存量
来源: https://www.studiobinder.com/blog/script-writing-on-youtube/

## 专业视频制作的 "Pre-Production 50% 法则"

1. **头脑风暴** — 明确主题与受众
2. **脚本撰写** — 口语化改写，每一句都有视觉锚点
3. **故事板/分镜** — 逐场景画出来，定义画面+声音+情绪
4. **素材准备** — 图库 / AI生成 / B-roll / 屏幕录制 / 动画
5. **才进入生产**

## 视觉多元化策略

专业人员不会 6 个场景全是纯色渐变+白字。需要:

| 画面类型 | 用途 | 工具 |
|----------|------|------|
| 纯文字卡 | 强调关键观点 | 渐变/电影级背景 |
| B-roll 素材 | 填充叙述段落 | Pexels/Pixabay/自拍 |
| 动画示意 | 解释抽象概念 | Manim/Motion Graphics |
| AI 生成图 | 无法实拍的画面 | ComfyUI/DALL-E/Sora |
| 屏幕录制 | 教程/演示 | QuickTime/OBS |
| 原文章配图 | 文章自带插图 | 直接使用 |

## 我们 v2 管线的分层设计

对应专业流程的四层:

```
Layer 0: Article Analysis (新)
  → preprod.py: analyze_article()
  → 提取: 段落数/总字数/建议场景数

Layer 1: Script Adaptation (新)
  → preprod.py: structure_scenes()
  → 关键词→视觉类型推断, 情绪推断

Layer 2: Storyboarding (新)
  → preprod.py: generate_storyboard()
  → 输出 storyboard.json (场景+视觉类型+情绪+时长)

Layer 3: Visual Production (升级)
  → visual/producer.py: VisualProducer
  → 6 种视觉类型: gradient_text / cinematic_text / 
    tech_abstract / motion_infographic / ai_concept_art / corporate_visual

Layer 4: Post-Production (新)
  → postproc.py: generate_srt() + burn_subtitles() + mix_bgm() + apply_transitions()
  → 字幕 + BGM + 交叉淡化转场
```

## 下一阶段（v3）改进方向

1. AI 自动生成分镜图（替换 ai_concept_art 的纹理站位）
2. B-roll 素材库集成（Pexels API 自动匹配）
3. 真正的脚本改编（调用 LLM 做口语化改写，当前是启发式）
4. 多 Agent 协作（Director/Writer/Artist 分工）
