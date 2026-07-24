# ocr_finance.py — 截图 OCR → 归集流动 全自动管线

## 文件位置

主脚本位于：`/Users/mac/.hermes/adjutant/finance/scripts/ocr_finance.py`

不入 skill 目录（太大，且是独立脚本需要被 Hermes 工具引用）。本文件仅为指向性参考。

## 调用方式

```bash
python3 /Users/mac/.hermes/adjutant/finance/scripts/ocr_finance.py <图片路径> [--dry-run] [--creditor "平台名"]
```

## 包含的 Hermes 工具

```bash
finance_ocr(image_path="...", creditor="拿去花", dry_run=False)
```

工具文件：`/Users/mac/.hermes/hermes-agent/tools/finance_ocr_tool.py`
注册位置：`/Users/mac/.hermes/hermes-agent/toolsets.py` → `_HERMES_CORE_TOOLS`

## 7步流程（代码级稳定，无 LLM 发挥）

| 步骤 | 功能 | 稳定手段 |
|------|------|---------|
| 1 | API Key 自检 | 环境变量 → .env 文件两级 fallback |
| 2 | API 连通性测试 | 401/403 → 明确报错"余额不足请充值" |
| 3 | OCR 识别 | 固定 prompt, temperature=0, 硬编码 endpoint+model |
| 4 | 债务匹配 | 名字模糊匹配 → 金额兜底 |
| 5 | 金额验证 + 更新 | >0 且 <¥100 万，原子写入(.tmp替换) |
| 6 | 同步 repo + 游戏化 | shutil.copy2 + subprocess |
| 7 | Git push | 全自动 add+commit+push |

## 2026-07-22 全链路验证结果

全部 7/7 步骤通过，Git push 成功。
