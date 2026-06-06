# OCR v3.0 双引擎架构

## 引擎堆栈

```
截图输入
    │
    ├─→ ocr_orchestrator.py (编排器)
    │       │
    │       ├─→ Apple Vision Pro (ocr_pro.swift)
    │       │     • Revision 3 (CJK optimized, macOS 13+)
    │       │     • Lanczos 2× 缩放
    │       │     • CIImageAutoAdjustmentOption.enhance
    │       │     • CIUnsharpMask (radius=1.2, intensity=0.8)
    │       │     • min confidence threshold: 0.2
    │       │
    │       └─→ EasyOCR (Python, 1.7.2)
    │             • CRAFT text detector
    │             • CRNN recognizer (ch_sim + en)
    │             • GPU: false (MPS compatibility)
    │
    └─→ 输出: JSON
          {
            "engines": {
              "apple_vision": {...},
              "easyocr": {...}
            },
            "comparison": {
              "common_numbers": [...],
              "flagged_amounts": [...],
              "agreement_rate": 0.X
            },
            "recommendation": "auto_accept" | "human_review"
          }
```

## 推荐策略

| 条件 | 动作 |
|------|------|
| 双引擎一致 + 无差异金额 | auto_accept → 直接更新 debts.json |
| 有差异金额 | human_review → 展示两个结果给波总确认 |
| Apple Vision 不可用 | 降级到 EasyOCR 单独输出 |
| 全部不可用 | 降级到 Tesseract（需波总确认金额） |

## 脚本位置

- `~/.hermes/scripts/ocr_pro.swift` — Apple Vision Pro
- `~/.hermes/scripts/ocr_orchestrator.py` — 双引擎编排器
- 各 profile 的 `scripts/` 目录也有副本

## 已知 Tesseract 缺陷（已降级为紧急备选）

- 数字 5 误读为 9（如 5303 → 9303）
- 开头 "1" 被吞（如 19432 → 9432）
- 中文字符误读（如 "剩余待还" → "简余待还"）
