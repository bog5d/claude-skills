---
name: ocr-screenshot-extraction
description: 当主模型不支持 vision（如 DeepSeek）、用户发送聊天截图/文档截图时，用 Tesseract OCR 提取中文文字。macOS 完整安装 + 使用流程。
category: productivity
trigger: user sends screenshot, vision_analyze fails, model doesn't support vision
---

# OCR Screenshot Extraction

## 🚨 执行顺序铁律（最高优先级，2026-08-19 与 Cursor 铁律统一）

**收到图片任务的第一步永远是：派 Cursor（原生多模态，精度最高）。只有 Cursor 不可用时才走下面的千问链路。**

```
步骤0：派 Cursor CLI（传图片绝对路径）→ 完成则标注 🔴 [Cursor 输出]
步骤1（Cursor 不可用时）：直调硅基流动千问 API（auxiliary.vision = custom:siliconflow, Qwen/Qwen3-VL-32B-Instruct，base64 直调 https://api.siliconflow.cn/v1/chat/completions）
步骤2：如果 API 401/403/超时 → 确认 API key 状态
步骤3：如果 key 不可用 → Firecrawl parse（云端 OCR，中文精度高）
步骤4：如果 Firecrawl MCP 未连接 → 告知用户「千问 key 失效 + Firecrawl 不可用」
步骤5：仅在用户明确说「用本地 OCR」后降级到 Apple Vision / EasyOCR / Tesseract
```

**🔴 绝对禁止（每次违反都被波总骂）：**
- ❌ 直接采信 Telegram 消息里平台自动附带的内置描述文本（`[The user sent an image~ Here's what I can see: ...]`）——必须主动走步骤0/1
- ❌ 跳过 Cursor 直接千问——Cursor 优先是第一条铁律
- ❌ 跳过千问直接 Tesseract/Apple Vision——中文几乎必乱码
- ❌ 小字/卡片/截图细节不放大就下结论——位置卡片等先裁剪 3× 放大再送千问精读，两轮结果不一致以放大精读为准

> **波总铁律（2026-06-09 定，2026-07-22、2026-08-19 多次重申）**：执行优先级 = Cursor CLI → 硅基流动千问 → Firecrawl → 本地 OCR。内置识别是最后手段，不是默认路径。

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
- **PDF 文档（议程/邀请函/扫描件）→ 走 `pdf-image-extraction` 技能**（三步法：get_text → 渲染页面 → 千问 VL）

## 本地 OCR（Qwen-VL-Max 不可用时的降级方案）

### 🥈 Firecrawl Parse（云端 OCR，优先于本地）

Firecrawl 的 parse 端点支持图片/PDF 文件上传并做 LLM 驱动的 OCR 提取。**中文识别精度远高于 Tesseract**，是千问 VL 不可用时的首选降级。

```json
// Phase 1: 上传文件 → 获取 uploadRef
{
  "name": "firecrawl_parse",
  "arguments": {
    "filePath": "/absolute/path/to/image.jpg",
    "contentType": "image/jpeg",
    "formats": ["json"],
    "jsonOptions": {
      "prompt": "识别并提取图中所有中文和英文文字，保留原始排版。",
      "schema": { "type": "object", "properties": { "text": { "type": "string" } } }
    }
  }
}
// Phase 1 返回 → 本地执行 curl 上传命令
// Phase 2: 用 uploadRef 获取结果
{
  "name": "firecrawl_parse",
  "arguments": {
    "uploadRef": "<phase-1-upload-ref>",
    "formats": ["json"],
    "jsonOptions": { ... }
  }
}
```

⚠️ **前提条件**：Firecrawl MCP 必须已连接（`hermes mcp status` 检查）。未连接时跳过此步，直接降级到下方本地方案。

### 🥉 本地 OCR 引擎

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

### 🥉 Tesseract（仅紧急备选 — 必须预处理）

**裸跑 Tesseract 中文几乎必乱码**，必须走预处理管线才能获得可用结果。

#### 预处理脚本（Python PIL，一行命令）

```bash
python3 -c "
from PIL import Image, ImageEnhance, ImageFilter
img = Image.open('/path/to/screenshot.jpg')
img = img.resize((img.width*2, img.height*2), Image.LANCZOS)   # 2× 放大
img = ImageEnhance.Contrast(img).enhance(2.0)                    # 对比度翻倍
img = img.filter(ImageFilter.SHARPEN)                             # 锐化
img.save(os.path.expanduser('~/ocr_preprocessed.png'))
"
```

#### ⚠️ macOS sandbox 陷阱

Tesseract 在 macOS 上**无法读取 /tmp 目录**（sandbox 限制），预处理后的图片必须存到 `~/` 下：
```bash
# ❌ 错误：存 /tmp，Tesseract 报 "image file not found"
# ✅ 正确：存 ~/ 或项目目录
tesseract ~/ocr_preprocessed.png stdout -l chi_sim+eng
```

#### Tesseract 固有缺陷（预处理后仍有）

- 数字 5→9 误读，开头 "1" 被吞
- 中文字符误读（如 "剩余待还" → "简余待还"）
- 金额类数据**必须人工确认**，不可直接入库
- 详细预处理配方 + 效果对比见 `references/tesseract-preprocessing.md`
