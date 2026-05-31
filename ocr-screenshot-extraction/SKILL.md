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

## 使用

```bash
python3 -c "
import pytesseract
from PIL import Image
img = Image.open('/path/to/screenshot.jpg')
text = pytesseract.image_to_string(img, lang='chi_sim+eng')
print(text)
"
```

## 注意
- 聊天截图通常 576x1280 左右，竖屏
- `chi_sim+eng` 同时识别中文和英文
- OCR 结果会有少量识别错误（如把 "王总" 识别成 "王总"，把特殊符号识别错），需结合上下文修正
- 图片路径通常在 `/Users/mac/.hermes/image_cache/img_*.jpg`
- 如果聊天记录跨多屏，可能需要用户发送多张截图
