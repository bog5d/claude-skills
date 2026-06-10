---
name: ocr-screenshot-extraction
description: 当主模型不支持 vision（如 DeepSeek）、用户发送聊天截图/文档截图时，用 Tesseract OCR 提取中文文字。macOS 完整安装 + 使用流程。
category: productivity
trigger: user sends screenshot, vision_analyze fails, model doesn't support vision
---

# OCR Screenshot Extraction

## 🥇 首选路径：通义千问 Qwen-VL-Max（云端视觉，唯一推荐）

**波总铁律（2026-06-09）：图片识别默认用千问 VL Max，不用 Tesseract/Apple Vision。**

当主模型不支持 vision（如 DeepSeek）时，Hermes 自动 fallback 到 `auxiliary.vision` 配置的模型。**Qwen-VL-Max 是国内中文图片识别最强模型**——直接理解图片内容，无需 OCR 中间层。

## 🥇 首选路径：通义千问 Qwen-VL-Max（云端视觉，默认）

当主模型不支持 vision（如 DeepSeek）时，**必须优先用千问 VL Max**，不要用 Tesseract/Apple Vision。千问直接理解图片内容，无需 OCR 中间层，中文识别精度远超本地方案。

> **波总铁律（2026-06-09）**：以后识别图片文字默认用千问 VL Max。Tesseract/Apple Vision 仅作千问不可用时的降级备选。

### 配置方法

在 profile `config.yaml` 的 `auxiliary.vision` 中设置：

```yaml
auxiliary:
  vision:
    provider: dashscope
    model: qwen-vl-max
    api_key: <阿里云百炼 API Key，完整 35+ 字符>
```

API Key 获取：https://dashscope.aliyun.com → 开通 Qwen-VL-Max 模型。

### ⚠️ 已知陷阱（2026-06-10 教训）

1. **API Key 截断**：Hermes 的 credential scanner 会将 config 中的 key 显示为 `sk-2ee...28b8`，但实际文件必须包含完整 key（~35 字符）。若写入时被 scanner 拦截导致只写了截断版（13 字符），API 会返回 `invalid_api_key`。验证方法：
   ```bash
   python3 -c "import yaml; k=yaml.safe_load(open('/Users/mac/.hermes/config.yaml'))['auxiliary']['vision']['api_key']; print(f'len={len(k)}')"
   # 正确应为 ~35，错误为 ~13
   ```

2. **Gateway 重启**：配置写入后需重启对应 gateway 才能生效。`vision_analyze` 工具在 gateway 重启前仍走旧配置。不能重启当前对话所在的 gateway（会断连）。

3. **直调绕过**：当 gateway 未重启但急需用千问时，可直接用 Python requests 调 DashScope API：
   ```python
   import yaml, base64, requests
   with open('/Users/mac/.hermes/config.yaml') as f:
       key = yaml.safe_load(f)['auxiliary']['vision']['api_key']
   with open('image.jpg', 'rb') as f:
       img_b64 = base64.b64encode(f.read()).decode()
   resp = requests.post('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
       headers={'Authorization': f'Bearer {key}'},
       json={'model': 'qwen-vl-max', 'messages': [{'role': 'user', 'content': [
           {'type': 'text', 'text': '提取所有文字'},
           {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}}
       ]}]})
   print(resp.json()['choices'][0]['message']['content'])
   ```

### 同步到所有 profile（一次性）

```bash
/Users/mac/.hermes/hermes-agent/venv/bin/python3 -c "
import yaml; key='<完整key>'
for prof in ['her-m2','default','english-tutor','finance']:
    p=f'/Users/mac/.hermes/profiles/{prof}/config.yaml' if prof!='default' else '/Users/mac/.hermes/config.yaml'
    with open(p) as f: cfg=yaml.safe_load(f)
    cfg['auxiliary']['vision']={'provider':'dashscope','model':'qwen-vl-max','api_key':key}
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
