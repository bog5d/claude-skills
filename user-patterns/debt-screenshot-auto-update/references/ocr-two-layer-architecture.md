# OCR 双层架构

## 架构总览（2026-07-25 重写）

```
scripts/
├── siliconflow_ocr.py    ← 纯通用 OCR
│   Prompt: "提取图中所有可视文字"
│   输出: {full_text, amounts, dates, list_items}
│   不假设任何业务场景
│
└── ocr_finance.py         ← 薄财务包装
    1. 调 siliconflow_ocr.py 做通用 OCR
    2. guess_page_type() 自动判断 balance/history
    3. match_platform() 匹配债务条目
    4. 更新 debts.json / transactions.json
    5. git push
```

## 设计原则

波总明确要求：OCR 就是 OCR，判断归判断。siliconflow_ocr.py 不假设任何业务场景，
只做一件事——把图上所有文字完整提取出来。

## 调试

```bash
python3 ocr_finance.py screenshot.jpg --raw
python3 siliconflow_ocr.py screenshot.jpg --verbose
```
