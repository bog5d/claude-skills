---
name: ocr-screenshot-extraction
description: 当主模型不支持 vision（如 DeepSeek）、用户发送聊天截图/文档截图时，用 Tesseract OCR 提取中文文字。macOS 完整安装 + 使用流程。
category: productivity
trigger: user sends screenshot, vision_analyze fails, model doesn't support vision
---

# OCR Screenshot Extraction

## 🚨 执行顺序铁律（最高优先级）

**收到中文文字图片的流程必须严格遵守以下顺序，一步不许跳：**

```
步骤1：直接调用 vision_analyze（走 auxiliary.vision → Qwen-VL）
步骤2：如果 vision_analyze 返回 401/403/超时 → 确认 API key 状态
步骤3：如果 API key 确实不可用 → 告知用户「千问 API key 已失效，请提供新 key」
步骤4：仅在用户明确说「放弃千问，用本地 OCR」后才降级到 Tesseract/Apple Vision
```

**绝对禁止的操作路径（每次违反都被波总骂）：**
- ❌ 「先用 Tesseract 试试看能不能读出来」——中文几乎必乱码，纯浪费时间
- ❌ 跑 3+ 次不同参数的 Tesseract 再切千问——在第一步就该用千问
- ❌ 在 skill 已经写明千问优先的情况下仍走老路径

> **波总铁律（2026-06-09，多次重申至 2026-07-14）**：图片文字识别默认用千问 VL。不要先尝试 Tesseract/Apple Vision。千问直接理解图片内容，无需 OCR 中间层，中文识别精度远超本地方案。

## 🥇 首选路径：通义千问 Qwen-VL-Max（云端视觉，唯一推荐）

当主模型不支持 vision（如 DeepSeek）时，Hermes 自动 fallback 到 `auxiliary.vision` 配置的模型。**Qwen-VL-Max 是国内中文图片识别最强模型**——直接理解图片内容，无需 OCR 中间层。

### 配置方法

波总实际使用硅基流动（SiliconFlow）调用千问视觉模型。有两种配置路径：

#### 路径 A：硅基流动 OpenAI 兼容接口（波总实际使用）

```yaml
auxiliary:
  vision:
    provider: openai
    model: Qwen/Qwen3-VL-32B-Instruct
    base_url: https://api.siliconflow.cn/v1
    api_key: <SiliconFlow API Key，sk- 开头>
```

API Key 获取：https://siliconflow.cn → 注册/登录 → API 密钥管理。

#### 路径 B：阿里云百炼原生接口（备选）

```yaml
auxiliary:
  vision:
    provider: dashscope
    model: qwen-vl-max
    api_key: <阿里云百炼 API Key>
```

API Key 获取：https://dashscope.aliyun.com → 开通 Qwen-VL-Max 模型。

### ⚠️ 已知陷阱

1. **调用前先确认实际配置**：用户说"我用硅基流动"，不等于 config 里确实配了硅基流动。收到图片后第一步应检查 `auxiliary.vision` 的实际 provider：`hermes config show` 或读取 config.yaml 相关段。**不要假设配置与用户说法一致然后盲目调用**（2026-07-14 教训：用户说硅基流动，实际 config 是 `provider: alibaba, api_key: ''`）。

2. **Gateway 重启**：配置写入后需重启对应 gateway 才能生效。`vision_analyze` 工具在 gateway 重启前仍走旧配置。不能重启当前对话所在的 gateway（会断连）。

3. **直调绕过**：当 gateway 未重启但急需用时，可直接用 Python requests 调 SiliconFlow / DashScope API：
   - SiliconFlow: POST `https://api.siliconflow.cn/v1/chat/completions`，Bearer token，model=`Qwen/Qwen3-VL-32B-Instruct`
   - DashScope: POST `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`，Bearer token，model=`qwen-vl-max`
   传 base64 图片即可。

### 同步到所有 profile（一次性）

```bash
/Users/mac/.hermes/hermes-agent/venv/bin/python3 -c "
import yaml
PROVIDER = 'openai'        # SiliconFlow: 'openai' | DashScope: 'dashscope'
MODEL = 'Qwen/Qwen3-VL-32B-Instruct'  # SiliconFlow | DashScope: 'qwen-vl-max'
BASE_URL = 'https://api.siliconflow.cn/v1'  # SiliconFlow 需设 | DashScope 设 None
API_KEY = '<完整key>'
for prof in ['her-m2','default','english-tutor','finance']:
    p=f'/Users/mac/.hermes/profiles/{prof}/config.yaml' if prof!='default' else '/Users/mac/.hermes/config.yaml'
    with open(p) as f: cfg=yaml.safe_load(f)
    vision_cfg = {'provider': PROVIDER, 'model': MODEL, 'api_key': API_KEY}
    if BASE_URL: vision_cfg['base_url'] = BASE_URL
    cfg['auxiliary']['vision'] = vision_cfg
    with open(p,'w') as f: yaml.dump(cfg,f,default_flow_style=False,allow_unicode=True,sort_keys=False)
"
```

### 工作原理

- 主模型对话 → DeepSeek 不变
- 波总发截图 → `vision_analyze` 自动走 Qwen-VL-Max
- **零手动切换**，对用户透明

---

## 触发条件
- 用户在 Telegram 发送截图/聊天记录图片
- `vision_analyze` 自动路由到 `auxiliary.vision` 模型
- 主模型（DeepSeek）不支持 vision

## 本地 OCR（Qwen-VL-Max 不可用时的降级方案）

以下方案仅在通义千问不可用时使用。

### 安装（一次性）

```bash
# macOS
brew install tesseract
brew install tesseract-lang   # 中文语言包，685MB
```

验证：
```bash
tesseract --list-langs | grep chi_sim   # 应输出 chi_sim
```

## OCR 引擎（v3.0 — 2026-06-06 升级）

详见 `references/ocr-v3-architecture.md` — 完整双引擎架构文档。

### 🥇 双引擎编排器（推荐）
```bash
python3 /Users/mac/.hermes/scripts/ocr_orchestrator.py /path/to/screenshot.jpg
```
输出 JSON，含 Apple Vision Pro + EasyOCR 双结果对比 + auto_accept/human_review 建议。

⚠️ **已知坑**：EasyOCR 可能未安装（`ModuleNotFoundError: No module named 'easyocr'`）。如果编排器因为 EasyOCR 缺失而失败，**直接用 Apple Vision Pro 单引擎**（见下方 🥈）。

### 🥈 Apple Vision Pro（快速模式 — 最可靠）
```bash
swift /Users/mac/.hermes/scripts/ocr_pro.swift /path/to/screenshot.jpg
```
Vision Revision 3 + Lanczos 2× 缩放 + 自动增强 + 锐化。**无需任何 Python 依赖，macOS 原生可用。**

### 🥉 EasyOCR（需额外安装）
```python
reader = easyocr.Reader(["ch_sim", "en"]); reader.readtext("/path/to/img.jpg")
```

### ⚠️ Tesseract（仅紧急备选）
数字 5→9 误读，开头 "1" 被吞。金额需波总确认。
