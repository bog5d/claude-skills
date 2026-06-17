# 全 Profile 模型统一降级为 Agnes + v4-flash

**日期**: 2026-06-17
**场景**: 副官 cron 消耗 98.5% 费用，用户要求全面降本
**操作**: 暂停 4 个低价值 cron + 修改 3 个 profile fallback 从 v4-pro → v4-flash

## 操作步骤

### 1. 暂停低价值 cron
```bash
hermes cron list
hermes cron pause 04fed24cbca2  # Q3 主动感知引擎
hermes cron pause a1582da9a8fa  # 飞书→副官 任务同步
hermes cron pause 85ba4bf2c1a9  # 每日健康巡检
hermes cron pause 1fa49ed0087e  # 财务中枢 周日晚大盘
```

### 2. 修改 profile fallback
finance 和 english-tutor 原本 fallback 是 v4-pro，改为 v4-flash：
```bash
hermes config set --profile finance fallback.provider deepseek-v4-flash
hermes config set --profile english-tutor fallback.provider deepseek-v4-flash
```

holo-local 原本无 fallback，新增：
```bash
hermes config set --profile holo-local fallback.provider deepseek-v4-flash
```

### 3. 验证
```bash
for p in default her-m2 finance english-tutor holo-local; do
  echo "=== $p ==="
  grep -A3 'default:' ~/.hermes/profiles/$p/config.yaml 2>/dev/null || echo "no config"
done
```

## 结果
- 所有 profile 统一：默认 agnes-2.0-flash（免费）→ fallback deepseek-v4-flash
- 4 个 cron 已暂停，不再产生无效调用
- 预计 token 费用下降 90%+
