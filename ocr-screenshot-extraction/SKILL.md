---
name: ocr-screenshot-extraction
description: 当主模型不支持 vision（如 DeepSeek）、用户发送聊天截图/文档截图时，用 Tesseract OCR 提取中文文字。macOS 完整安装 + 使用流程。
category: productivity
trigger: user sends screenshot, vision_analyze fails, model doesn't support vision
---

# OCR Screenshot Extraction

## 触发条件
- 用户在 Telegram 发送截图/聊天记录图片
- `vision_analyze` 返回不支持或报错
- 主模型（DeepSeek）不支持 vision

## 安装（一次性）

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

### 🥈 Apple Vision Pro（快速模式）
```bash
swift /Users/mac/.hermes/scripts/ocr_pro.swift /path/to/screenshot.jpg --preprocess
```
Vision Revision 3 + Lanczos 2× 缩放 + 自动增强 + 锐化。

### 🥉 EasyOCR
```python
reader = easyocr.Reader(["ch_sim", "en"]); reader.readtext("/path/to/img.jpg")
```

### ⚠️ Tesseract（仅紧急备选）
数字 5→9 误读，开头 "1" 被吞。金额需波总确认。
