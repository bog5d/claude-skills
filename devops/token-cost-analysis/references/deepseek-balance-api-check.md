# DeepSeek 官方账户余额查询（API 直查）

当用户收到余额预警短信/通知时，第一步先查官方余额，再深入分析账单。

## 查询余额

```bash
curl -s https://api.deepseek.com/balance \
  -H "Authorization: Bearer YOUR_API_KEY"
## 查询余额

```bash
curl -s https://api.deepseek.com/balance \
  -H "Authorization: Bearer YOUR_API_KEY"
```

返回格式：
```json
{"balanceInfo": [{"currency": "CNY", "balanceAmount": "29.37"}]}
```

## 欠费状态

如果返回 HTTP 402 或余额为负数（如 -¥0.84），说明账户已欠费，需立即：
1. 充值恢复服务
2. 排查费用来源（见 copilot-acp-retry-loop.md）
3. 设置消费限额

## 诊断命令

```bash
# 查余额（注意：如果 key 已欠费，可能返回 402）
curl -s https://api.deepseek.com/balance -H "Authorization: Bearer YOUR_KEY" | python3 -m json.tool

# 查用户信息（含额度）
curl -s https://api.deepseek.com/user/info -H "Authorization: Bearer YOUR_KEY" | python3 -m json.tool
```

## 关键信号

| 余额状态 | 含义 | 行动 |
|----------|------|------|
| 正常但账单高 | 用量确实大，需分析哪个 key/model | 看 CSV 账单 |
| 欠费/0 | 有未计费的调用或已耗尽 | 立即停 copilot-acp |
| 部分 key 欠费 | 多 key 独立计费 | 隔离 billing key |

## 2026-06-19 实际调用记录

- 余额 ¥29.37（昨晚刚充，一晚上花了几十）
- 近三天日均 ¥66.9
- gateway.error.log 中有 `HTTP 402: Insufficient Balance` 记录
- token_ledger 只显示 agnes 费用（¥0），账单和内部日志严重脱节
