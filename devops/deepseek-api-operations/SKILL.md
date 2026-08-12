---
name: deepseek-api-operations
description: Verify DeepSeek model version, balance, or pricing.
tags: [deepseek, model, version, alias, balance, pricing, api, reconfigure]
---

# DeepSeek API 版本与余额运营

回答「我连的是不是最新模型」「要不要重新配置」以及查余额/价格时的标准打法。

## 核心机制：稳定别名（最重要）

DeepSeek 的 API model id（`deepseek-v4-pro`、`deepseek-v4-flash`）是**稳定别名**，后台滚动指向最新权重。版本号（如 `-0813`、`-0731`）是**权重版本号，不是 API model id**，对调用方完全透明。

**结论：DeepSeek 每次发新版（如 V4-Pro-0813），用户零配置** —— model id 不变、base_url 不变、调用方法不变，已自动吃到最新权重。永远不要因为「发了新版」去改 config.yaml。

## 判断「是否最新版」的正确顺序

1. **`/models` 端点只返回稳定别名**（永远没有版本后缀）：
   ```bash
   curl -s https://api.deepseek.com/v1/models -H "Authorization: Bearer $KEY"
   # => [{"id":"deepseek-v4-flash"}, {"id":"deepseek-v4-pro"}]   ← 不会有 -0813
   ```
   → 无法从 API 侧验证到具体权重快照，这是预期行为。

2. **官方定价页的 `MODEL VERSION` 列是权威来源**：
   `https://api-docs.deepseek.com/quick_start/pricing/`
   页面直接标注每个别名的当前权重版本（`deepseek-v4-pro` → `DeepSeek-V4-Pro-0813`），并含价格表 + 涨价脚注（如 "significant increase expected"）。抓价格：`curl -s <url> | grep -oE '\$0\.[0-9]+'` 拿到 6 个数字（顺序稳定）。

3. **官方 Change Log**：`https://api-docs.deepseek.com/updates/`
   每次发版的标准句式（都是这句）：*"The API calling method remains unchanged — simply set the model name to `deepseek-v4-xxx` to use the latest version."*

## 余额端点

`GET https://api.deepseek.com/user/balance`（是 `/user/balance`，**不是** `/balance`，后者 404）。

```json
{"is_available":true,"balance_infos":[{"currency":"CNY","total_balance":"88.72","granted_balance":"0.00","topped_up_balance":"88.72"}]}
```
- `total_balance` 总余额 / `granted_balance` 赠送 / `topped_up_balance` 充值。
- **DeepSeek 无按模型/按天用量明细的公开 API** —— 只给余额。逐日拆解靠本地 `~/.hermes/logs/token_ledger.jsonl` 或控制台导出 CSV。

## 价格监控 watchdog

官方定价页可 curl 抓 6 个价格数字（顺序稳定）：
`0.0028(flash hit), 0.003625(pro hit), 0.14(flash miss), 0.435(pro miss), 0.28(flash out), 0.87(pro out)`

做法：no_agent cron 每日抓定价页，diff 这 6 个数字 vs 本地快照 `~/.hermes/cache/documents/ds_price_snapshot.json`，任何变化 → 告警（涨价落地即触发）；余额跌破阈值 → 提醒充值；无变化 → 静默（空输出）。已部署脚本：`~/.hermes/profiles/her-m2/scripts/ds_price_watchdog.py`（cron `0fe9f00458b8`，每日 09:00，零 LLM）。

## Pitfalls

- **不要因为 DeepSeek 发了新版就去改 model id** —— 稳定别名机制保证零配置。改 model id 反而是错的。
- **查「最新版」别用 `/models`** —— 它不返回版本号，会误判「不是最新」。用定价页 `MODEL VERSION` 列。
- **余额端点是 `/user/balance`**，带 `user` 前缀；裸 `/balance` 404。
- **`web_extract` 后端是 ddgs（search-only，不能抓 URL 正文）** → 抓 DeepSeek 文档页用 firecrawl `mcp__firecrawl__firecrawl_scrape`（`formats=["markdown"]`）。
- **token_ledger 可能滞后断档**（model_governance 记账停了就停更）——最新余额永远以 `/user/balance` 为准，不要拿过期的 token_ledger 当当前账。

## 相关（bundled，不可直接编辑，但知识互补）

- `token-cost-analysis` — 账单异常诊断、缓存命中率、多源账单脱节
- `profile-model-routing` — 各 profile 的 model/fallback 配置
- `deepseek-cache-optimization` — 前缀缓存优化
