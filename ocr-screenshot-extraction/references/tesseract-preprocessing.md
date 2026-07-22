# Tesseract 中文 OCR 预处理配方

## 问题

裸跑 Tesseract 对手机截图（576×1280 级别）的中文识别几乎不可用——数字乱码、中文字符误读严重。

## 根因

1. 手机截图分辨率偏低（72 DPI，576×1280），Tesseract 需要 ≥300 DPI
2. 低对比度导致文字与背景混淆
3. macOS sandbox 阻止 Tesseract 读取 `/tmp` 目录下的文件

## 预处理管线（已验证有效 — 2026-07-22）

```python
from PIL import Image, ImageEnhance, ImageFilter

img = Image.open('/path/to/screenshot.jpg')
img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)  # 2× → 1152×2560
img = ImageEnhance.Contrast(img).enhance(2.0)                       # 对比度翻倍
img = img.filter(ImageFilter.SHARPEN)                                # 锐化
img.save(os.path.expanduser('~/ocr_preprocessed.png'))
```

然后运行：
```bash
tesseract ~/ocr_preprocessed.png stdout -l chi_sim+eng
```

## sandbox 陷阱

```bash
# ❌ 存 /tmp → Tesseract 报 "Error opening data file /tmp/..."
tesseract /tmp/ocr_preprocessed.png stdout -l chi_sim+eng

# ✅ 存 home 目录
tesseract ~/ocr_preprocessed.png stdout -l chi_sim+eng
```

## 效果对比（同一张考研词汇 App 截图）

| 指标 | 裸 Tesseract | 预处理后 |
|------|-------------|---------|
| "今日忘记: 22" | 识别为 "今日忘记: 22" ✓ | 识别为 "今日忘记: 22" ✓ |
| "今日模糊: 21" | 乱码 | "今日模糊: 21" ✓ |
| "今日时长: 28 m" | 乱码 | "今日时长: 28 m" ✓ |
| 整体可读性 | ~40% | ~85% |
