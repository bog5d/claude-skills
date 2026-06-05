---
name: article-to-video-production
description: "公众号/技术文章转短视频——分镜脚本、TTS旁白、ffmpeg合成、质量标准。不是翻译，是再创作。"
category: creative
---

# Article → Video Production Pipeline

## 核心理念

**文章转视频不是"翻译"，是"再创作"。** 微信文章是读的，视频是看+听的。好的转换应该让观众"听+看一个独立的故事"，不是"瞪着眼睛读屏幕上的字"。

## 质量标准（四必须）

| 标准 | 说明 |
|------|------|
| 🥇 **必须有声音** | TTS 旁白 + 背景配乐。纯文字幻灯片 = 废品 |
| 🥈 **数字要动态** | 数据从低滚到高，不要静态表格。大字率 > 小表格 |
| 🥉 **开头有钩子** | 前 3 秒痛点/反常识/具体数字，不要放标题 |
| 4 | **节奏随内容** | 高潮快切，论述慢放，根据信息密度变化 |

## Pipeline

### Step 1: 写分镜（最关键）

每帧定义：`text`（旁白文字）、`big_text`（屏幕大标题）、`subtext`（副标题/补充）、`bg_color`（背景色）、`duration_extra`（留白秒数）。

原则：
- 7 帧是黄金数量（60-90 秒视频）
- 每帧 1-2 个核心信息点
- big_text < 25 字，大字率
- 帧号标记（01/07 → 07/07）放在右上角
- 最后帧必须有 CTA（GitHub 链接/公众号关注）

### Step 2: TTS 旁白

**首选 Edge TTS**（免费，零配置）：
```python
import edge_tts, asyncio
comm = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")  # 自然女声
asyncio.run(comm.save("output.mp3"))
```

可选语音：`zh-CN-YunxiNeural`（男声）、`zh-CN-XiaoyiNeural`（活泼女声）。

**MiniMax TTS**（需 JWT 格式 key，`sk-cp-` 前缀不可用）：
```python
# MiniMax key 必须是 eyJ... JWT 格式
# sk-cp-... 格式会返回 "login fail"
url = "https://api.minimax.chat/v1/t2a_v2"
# voice_id: "female-shaonv", "male-qn-qingse", etc.
```

### Step 3: 渲染视频帧

**首选：ffmpeg drawtext**

```bash
ffmpeg -y \
  -f lavfi -i "color=c=#0f0c29:s=1080x1920:d=8.5:r=30" \
  -i scene_01.mp3 \
  -vf "drawtext=text='主标题':fontsize=52:fontcolor=white:x=(w-tw)/2:y=h*0.3:fontfile=PingFang.ttc:shadowcolor=black@0.5:shadowx=3:shadowy=3,..." \
  -c:v libx264 -preset fast -crf 23 \
  -c:a aac -b:a 128k -shortest segment_01.mp4
```

**⚠️ macOS Homebrew ffmpeg 默认不带 drawtext**（缺 libfreetype）。检测：`ffmpeg -filters 2>&1 | grep drawtext`。无输出 = 不可用。

**Fallback：PIL/Pillow 逐帧渲染**（本会话验证通过）

```python
from PIL import Image, ImageDraw, ImageFont

FONT = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 52)

for fnum in range(total_frames):
    img = Image.new("RGB", (1080, 1920), (15, 12, 41))
    draw = ImageDraw.Draw(img)
    draw.text((center_x, 540), "主标题", font=FONT, fill="white")
    img.save(f"frame_{fnum:05d}.png")

# 编码：PNG 序列 + 音频 → MP4
ffmpeg -framerate 30 -i frame_%05d.png -i audio.mp3 \
  -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k \
  -shortest segment.mp4
```

PIL 方案优势：阴影、进度条、渐变、多行文字等完全可控，不依赖 ffmpeg 编译选项。

### Step 4: 拼接 + 压缩

```bash
# Concat
for f in segment_*.mp4; do echo "file '$f'" >> concat.txt; done
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy final.mp4

# 压缩（Telegram < 50MB）
ffmpeg -i final.mp4 -c:v libx264 -preset fast -crf 28 -c:a aac -b:a 64k compressed.mp4
```

## 分镜模板

```
01 🪝 钩子：痛点数字（"10件事只记3件 → 装上记8件"）
02 🔍 问题：为什么难（"三种方案，三种硬伤"）
03 🏗️ 方案：核心架构（"四层渐进记忆 L0→L1→L2→L3"）
04 🔗 亮点1：追溯链（"L3→L2→L1→L0 证据链不断裂"）
05 📐 亮点2：压缩（"Token -61%，完成率 +23%"）
06 📊 数据：跑分（"准确率 48→76%，召回 30→79%"）
07 🚀 CTA：一行命令（"开源地址搜 TencentDB-Agent-Memory"）
```

## Method C: HTML → Playwright Screenshot（设计感最强）

当需要 CSS 渐变背景、阴影、排版精致度远超 PIL 时使用。

### ✅ 推荐架构：Jinja2 模块化管线

**不要写"一个脚本硬扛全流程"**——CSS 和 Python 模板同居必定出 bug。用四层分离：

```
~/.hermes/tools/ai-qujing/
├── config.json              # 场景数据（TTS 文本、配色、字号）——改场景不动代码
├── templates/slide.html     # Jinja2 模板——CSS 零转义，天然隔离
├── tts.py                   # Edge TTS 语音合成
├── renderer.py              # Jinja2 渲染 → Playwright 截图
├── encoder.py               # ffmpeg 帧编码 + 多段合成
└── build.py                 # 编排器：读 config → TTS → 渲染 → 合片
```

**用法**：
```bash
cd ~/.hermes/tools/ai-qujing
python build.py                          # 读 config.json → output/config/
python build.py --config episode-03.json # 指定配置
python build.py --out /tmp/my-video      # 指定输出目录
```

**新文章只需改 `config.json` 的 `scenes` 数组**，不动任何 Python 代码。

### ⚠️ 旧方案：Playwright Python API 直接调用（仅备查）

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1080, "height": 1920})
    page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
    page.screenshot(path="screenshot.png", full_page=False)
    browser.close()
```

⚠️ **用 Python API，不要用 CLI**：`npx playwright screenshot` 在本机有 parser 错误，Python `playwright.sync_api` 稳定。

⚠️ **本地 HTML 必须用 `file://`**：`html_path.resolve().as_uri()` 生成 `file:///path/to/file.html`。

⚠️ **如果用 `.format()` 渲染模板，CSS 要双花括号**（见 Pitfall #6）。**建议直接改用 Jinja2，一劳永逸。**

## Pitfalls

1. **MiniMax `sk-cp-` key 不能用于 TTS**：MiniMax 有两种 key 格式。`sk-cp-` 前缀的 key 在 TTS API 返回 `status_code: 1004 login fail`。需要 JWT 格式 key（`eyJ...`）。建议用 Edge TTS 作为默认。
2. **ffmpeg drawtext 逗号问题**：`-vf` 参数中 drawtext 之间用逗号分隔。如果文字本身含逗号，会被误解析。用 `:text='...'` 单引号包裹。
3. **音频时长获取**：`ffprobe -v quiet -show_entries format=duration -of csv=p=0 audio.mp3`
4. **视频卡死**：`-shortest` 参数确保视频随音频结束，防止无声黑屏。
5. **Telegram 50MB 限制**：大于 50MB 需压缩，`-crf 28` 通常能压到 10-30MB。
6. **❌ Python `.format()` + CSS = 花括号地狱（应避免，用 Jinja2 替代）**：当 HTML 模板用 `.format(**kwargs)` 渲染时，CSS 里的 `{...}` 会被当作占位符。三个铁律：
   - **所有 CSS 规则块用 `{{...}}`**：`body {{ width:100%; }}` → 渲染后 `body { width:100%; }`
   - **CSS 内嵌的真实占位符保持单花括号**：`{{ margin-top:{big_top}px; }}` → 外层 `{{}}` 转义，内层 `{big_top}` 正常替换
   - **表达式不能写在花括号里**：`{W-120}` → KeyError。必须 `W120 = W - 120` 预计算后传入
   - 错误表现：`KeyError: ' margin'`（`* { margin:0 }` 没转义）、`KeyError: '\\n    width'`（`body {\n  width:...` 没转义）、`KeyError: 'W-120'`（表达式不被支持）
