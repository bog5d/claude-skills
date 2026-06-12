# consumption_deep_analysis.json Schema

## Purpose
12-month Alipay + WeChat consumption deep analysis for AI handoff. Generated from `financial_portrait_2025-06_to_2026-06.json` (2,722 transactions after filtering).

## When to generate
When 波总 asks for: "消费流水深度分析", "整合支付宝微信数据", "深度洞察", "过去一年消费打成JSON"

## Structure (10 sections)

### _meta
Sources, filtering rules, period, total transactions analyzed.

### overview
```
total_outflow_12m, total_outflow_ex_tax, total_tax, monthly_avg, peak/valley month,
by_platform, platform_share (alipay_pct, wechat_pct)
```

### category_ranking
All categories sorted by total descending. Each: `name, total, count, pct, monthly_avg, by_month{}`

### monthly_trend
13 months (2025-06 through 2026-06). Each: `total, count, platform_split, top_category, large_txns[]`

### relationship_flows
Four named relationships: spouse_dily, brother_carlo, mother_cuixiang, landlord_liuqin.
Each with: total_12m, merchants list, note (波总确认的注解), trend data.

### business_flows
Four categories: accounting(财驴), deregistration(企管家), intl_payment(Stripe), entertainment(足浴).
Each with: merchant, total, note (波总确认).

### top_merchants
Top 30 merchants by total spend. Array of {merchant, total}.

### deep_insights (5 sub-sections)
- income_profile: 收入推测 + 证据链
- consumption_pattern: 消费模式 + 证据
- mobility_fingerprint: 出差指纹 + 证据
- debt_repayment_behavior: 还债行为 + 证据
- risk_flags: 风险信号列表
- monthly_anomalies: 逐月异常标记

### recommendations (3 sub-sections)
- debt_priority: 还款优先级（critical/high/medium）
- cost_optimization: 成本优化建议 + 预估节省
- cash_flow: 现金流预警

### current_month + debt_context
June 2026 daily breakdown + consumption-vs-debt ratio analysis.

## Generation method
```bash
cd ~/.hermes/adjutant/finance
python3 << 'PYEOF'
# Read financial_portrait JSON + debts.json + expenses.json
# Reconstruct into the 10-section schema above
# Write to reports/consumption_deep_analysis.json
PYEOF
```

Key: always `git add -A && git commit && git push` after generation.
