# ocr_finance.py — 截图 OCR → 归集流动 全自动管线

## 文件位置

主脚本位于：`/Users/mac/.hermes/adjutant/finance/scripts/ocr_finance.py`

## 调用方式

```bash
source ~/.hermes/profiles/finance/.env
python3 ocr_finance.py <图片路径> [--dry-run] [--creditor "平台名"]
```

## 包含的 Hermes 工具

`finance_ocr(image_path="...", creditor="拿去花", dry_run=False)`

## 7步流程

| 步骤 | 功能 |
|------|------|
| 1 | API Key 自检 |
| 2 | API 连通性测试 |
| 3 | OCR 识别（Qwen3-VL） |
| 4 | 债务匹配 |
| 5 | 判断截图类型 + 更新 |
| 6 | 同步 repo + 游戏化 |
| 7 | Git push |

## 2026-07-25 重要修复：双截图类型支持

**问题：** 旧版只有一种模式——读到 remaining_amount 就 `diff = old - new` 当还款。余额概览页显示的是多笔还款累积后的余额变化，diff 不是单笔还款。

**修复：** OCR prompt 新增：
- `page_type`: "balance" | "history" | "unknown"
- `latest_payment_amount`: 最新一笔还款金额
- `latest_payment_date`: 最新一笔还款日期

**逻辑分支：**
- `page_type == "history"`: 提取 `latest_payment_amount` 直接记录单笔交易
  - 不同步更新 debts.json（除非同时有 remaining_amount）
- `page_type == "balance"` 或 fallback: 走老逻辑用 remaining_amount 更新余额

**注意：** 历史页 OCR 可能失败（复杂表格布局），千问VL偶尔返回空。此时：
1. 先试 --dry-run 预览
2. 不行就用 tesseract 垫底
3. 再不行让波总口述
