# DeepSeek 主动余额对账 — 部署与运维

## 概述

Hermes 部署了一套零人工的 DeepSeek 余额追踪管线：
- 每小时自动拉官方余额
- 每天 9:00 推送对账日报
- 异常消耗自动告警（翻倍/减半）

## 文件

| 文件 | 说明 |
|------|------|
| `~/.hermes/scripts/ds_cost_recon.py` | 对账引擎主脚本 |
| `~/.hermes/scripts/ds_daily_report.sh` | 日报包装脚本（传 `report` 参数） |
| `~/.hermes/cache/documents/ds_balance_log.json` | 余额历史数据 |

## Cron Jobs

```bash
# 每小时余额轮询（no_agent=true，零 LLM 成本）
cronjob: 05a3e44e8031
  schedule: 0 * * * *
  script: ds_cost_recon.py
  no_agent: true

# 每日对账日报
cronjob: c18f45b55200
  schedule: 0 9 * * *
  script: ds_daily_report.sh
  no_agent: true
```

## 数据格式

`ds_balance_log.json`:
```json
{
  "2026-06-26": {
    "snapshots": [
      {"time": "14:05", "balance": 46.48},
      {"time": "15:00", "balance": 46.12}
    ],
    "balance": 46.12,
    "currency": "CNY"
  }
}
```

迁移逻辑：自动将旧格式 `{"balance": 50.15, "currency": "CNY"}` 转为新格式（加 `snapshots` 数组）。

## 异常检测规则

| 条件 | 告警 |
|------|------|
| 日消耗 > 近7日均值 × 2 | 🚨 异常翻倍 |
| 日消耗 < 近7日均值 × 0.3 | ✅ 节省通知 |
| 余额 < ¥5 | ⚠️ 充值预警 |

## DeepSeek API

- **余额接口**: `GET https://api.deepseek.com/user/balance`
- **需要**: `Authorization: Bearer <key>`
- **返回**: `{"balance_infos": [{"total_balance": "46.48", "granted_balance": "0.00", "topped_up_balance": "46.48", "currency": "CNY"}]}`
- **不存在**: 消费明细账单接口（已测试 5 个候选 endpoint 均返回 404）

## 定价（DeepSeek V4-Pro 促销期）

| 项目 | 单价 (per 1M tokens) |
|------|------|
| Input (cache miss) | $0.435 |
| Input (cache hit) | $0.003625 |
| Output | $0.87 |

促销期后（2026-05-31 起）：$1.74 input, $3.48 output。

## 运维手册

### 健康检查
```bash
# 查看最近余额
python3 -c "import json; d=json.load(open('$HOME/.hermes/cache/documents/ds_balance_log.json')); days=sorted(d.keys()); print(f'最新: {days[-1]} ¥{d[days[-1]][\"balance\"]:.2f}')"

# 查看 cron 状态
cronjob(action='list') | grep -E '05a3e44e|18f45b55'
```

### 手动触发
```bash
python3 ~/.hermes/scripts/ds_cost_recon.py          # 拉余额
python3 ~/.hermes/scripts/ds_cost_recon.py report   # 出日报
```

### ⚠️ 常见故障

| 现象 | 原因 | 修复 |
|------|------|------|
| `KeyError: 'snapshots'` | 旧数据格式未迁移 | 脚本已自动处理，再跑一次即可 |
| API 返回 402 | 余额耗尽 | 通知波总充值 |
| API 返回 401 | Key 过期 | 更新 ~/.hermes/.env 中的 DEEPSEEK_API_KEY |
