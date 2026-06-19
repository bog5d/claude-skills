# Copilot ACP 死循环重试 — 2026-06-19 案例

## 现象
DeepSeek 控制台余额 ¥29.37（昨晚刚充），近三天日均 ¥66.9。token_ledger 只显示 agnes 费用（¥0），账单和内部日志严重脱节。

## 账单数据
- 6/17: ¥63.61 (v4-pro: ¥52.25, v4-flash: ¥11.36)
- 6/18: ¥81.28 (v4-pro: ¥62.75, v4-flash: ¥18.53)
- 6/19: ¥55.79 (v4-pro: ¥33.29, v4-flash: ¥22.51)
- 对比 6/15: ¥5.87, 6/16: ¥10.13

## 根因分析

### 1. Copilot ACP 无限重试循环
gateway.error.log 中发现大量：
```
WARNING agent.chat_completion_helpers: Non-streaming API call stale for 90s
WARNING agent.conversation_loop: API call failed (attempt 3/3)
error_type=TimeoutError provider=copilot-acp base_url=https://api.deepseek.com/v1 model=deepseek-v4-pro
```
- Cursor/Trae CN 通过 Copilot ACP 通道调用 DeepSeek
- 每次 90 秒超时 → 重试 3 轮 → 每轮都扣费
- token_ledger 中 6/18 一天 233 次 v4-pro 调用，187 万 input tokens
- 来源全是 `agent:telegram:task:*`（ACP 桥接通过 Telegram 触发）

### 2. 官方 DeepSeek 直连也在欠费
```
provider=deepseek base_url=https://api.deepseek.com/v1
HTTP 402: Insufficient Balance
```
另一个 key 直接调 `api.deepseek.com` 也欠费了。

### 3. token_ledger 不完整
只记录 Hermes 自身 agnes 请求，不记录 copilot-acp 和外部直调。

## 诊断命令
```bash
# 看 token_ledger 中 v4-pro 的调用源
grep 'deepseek-v4-pro' ~/.hermes/logs/token_ledger.jsonl | python3 -c "
import sys, json
from collections import defaultdict
sources = defaultdict(lambda: {'calls': 0, 'input': 0})
for line in sys.stdin:
    e = json.loads(line.strip())
    src = e.get('source','?').split(':')[2][:20]
    sources[src]['calls'] += 1
    sources[src]['input'] += e.get('input_tokens', 0)
for s, i in sorted(sources.items(), key=lambda x: -x[1]['calls']):
    print(f'{s}: {i[\"calls\"]} calls, input={i[\"input\"]:,} tok')
"

# 看 copilot-acp 超时重试次数
grep -c 'copilot-acp.*TimeoutError.*deepseek-v4-pro' ~/.hermes/logs/gateway.error.log

# 看 gateway 中所有 provider 调用
grep 'provider=' ~/.hermes/logs/gateway.error.log | grep -oP 'provider=\K[^ ]+' | sort | uniq -c | sort -rn
```

## 修复方案
1. 停用 copilot-acp provider（不需要 Cursor 通过 Hermes 调度 DeepSeek）
2. 暂停副官记忆仓同步（每 5 分钟高频 cron）
3. 检查 DeepSeek 官方 key 余额，隔离 billing

## 关键信号
- token_ledger 费用 ≈ 0 但 DeepSeek 控制台账单很高 → 有外部调用不走 Hermes
- gateway.error.log 中出现 `copilot-acp.*TimeoutError` 循环 → 死重试扣费
- 同一 model 在多个 provider/base_url 出现 → 多 key 烧钱
