---
name: cron-audit
version: 1.0
author: Hermes
tags: [cron, audit, optimization, cost-reduction, scheduled-tasks]
description: 审计 cron jobs 的活跃度、价值和使用频率，识别冗余/低价值任务并批量暂停或清理。
created: 2026-06-17
updated: 2026-06-17
---

# Cron Job 审计与精简

当用户提到"清理 cron"、"看看哪些任务没用"、"太频繁了"、"帮我精简一下"时使用。

## 触发条件

- 用户要求清理/精简 cron jobs
- 用户报告 token 费用过高，怀疑 cron 是原因
- 用户觉得某个 cron job 推送太多/太频繁
- 新会话接手时主动审计（预防性）

## 审计步骤

### 1. 列出所有活跃 cron jobs
```bash
python3 -c "
import json
with open('/Users/mac/.hermes/cron/jobs.json') as f:
    data = json.load(f)
for job in data['jobs']:
    if not job.get('enabled'):
        continue
    name = job.get('name','')
    no_agent = job.get('no_agent', False)
    profile = job.get('profile')
    script = job.get('script','')
    prompt = job.get('prompt','')[:60]
    schedule = job.get('schedule','')
    repeat = job.get('repeat')
    print(f'[{'no_agent' if no_agent else 'AI'}] {name} | profile={profile or 'default'} | schedule={schedule} | repeat={repeat}')
    print(f'    cmd: {script or prompt}')
"
```

### 2. 逐个评估价值

| 评估维度 | 判断标准 |
|---------|---------|
| **频率** | 每5分钟/30分钟跑一次的是否真的需要这么频繁？ |
| **产出** | 每次执行的结果是否有新价值？还是重复相同内容？ |
| **错误率** | 是否经常报错？报错超过3次考虑暂停 |
| **用户反馈** | 用户是否说过"别推了"/"太多了"？ |
| **依赖关系** | 其他 job 是否依赖它的输出？ |

### 3. 高风险信号（立即暂停）

- **感知引擎类**：每5-30分钟跑，产出全是"无新commit"/"无变化"
- **健康巡检类**：每天跑但一直报错，且无人修复
- **自动推送类**：用户从未反馈有用，或明确说过"别自动推"
- **低频但高频**：比如"周报"实际每天跑

### 4. 暂停操作

```bash
# 单个暂停
cronjob action=pause job_id=<id>

# 或直接改 jobs.json
python3 -c "
import json
with open('/Users/mac/.hermes/cron/jobs.json') as f:
    data = json.load(f)
for job in data['jobs']:
    if job['name'] == '<job_name>':
        job['enabled'] = False
        job['paused_at'] = '<date>'
        job['paused_reason'] = '<reason>'
with open('/Users/mac/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
"
```

### 5. 验证
```bash
cronjob action=list
```
确认暂停的 job 不再出现在 enabled 列表中。

## 保留原则

以下类型通常保留（除非用户明确要求）：
- **Gateway 健康看门狗**：基础设施底线
- **API 预算熔断守卫**：成本控制
- **日志轮转**：磁盘空间管理
- **Profile 唤醒注入**：her-m2 等开发线的上下文恢复
- **TDAI 备份/巡检**：外部系统维护

## Pitfalls

- 暂停前确认 job 的依赖关系——有些 job 可能是其他流程的输入
- `no_agent: true` 的脚本 job 不会消耗 LLM token，但消耗磁盘空间和 cron ticker CPU
- 暂停不等于删除——用户可以随时恢复（`cronjob action=resume`）
- 改 jobs.json 后**不需要**重启 gateway，scheduler 会热加载