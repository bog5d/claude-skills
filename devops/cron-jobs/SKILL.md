---
name: cron-jobs
description: Complete cron job management — scheduling, troubleshooting, auditing, env isolation, webhook subscriptions, and session-specific cron patterns.
---

# Cron 定时任务管理

## 1. 创建与管理

### 基本创建
```python
cronjob(
    action='create',
    name='任务名称',
    schedule='0 23 * * *',  # 或 '30m', 'every 2h', 'once in 5m'
    deliver='origin',  # 'origin', 'local', 'all', or 'platform:chat_id:thread_id'
    prompt='自包含的任务指令'
)
```

### 调度格式
- Cron 表达式：`0 9 * * *`（每天早9点）
- 相对：`30m`（每30分钟）、`every 2h`（每2小时）
- 一次性：`once in 5m`（5分钟后执行一次）
- ISO 时间戳：`2026-06-01T09:00:00`

### 关键配置
- `deliver`: 投递目标。`origin`=当前会话，`local`=仅保存不发送，`all`=所有频道，`platform:chat_id:thread_id`=指定频道
- `no_agent=True`: 纯脚本模式，无 LLM 消耗，stdout 直接投递
- `context_from`: 上游 job ID，注入最近完成输出作为上下文
- `skills`: 加载的技能列表，按顺序执行

## 2. 故障排查

### 标准排查流程
1. `cronjob action=list` — 检查任务状态和最后运行时间
2. 检查 `~/.hermes/cron/output/<job_id>/` 目录 — 查找执行记录
3. 读取日志文件 — `read_file path=~/.hermes/cron/output/<job_id>/<timestamp>.md`
4. 分析错误模式（见下方常见错误表）

### 常见错误
| 错误 | 原因 | 解决 |
|------|------|------|
| HTTP 502 | 网关/API 暂时不可用 | 重试，检查网络 |
| API call failed after 3 retries | 网络或认证问题 | 验证 API 密钥 |
| Job not found | 任务已删除 | 重新创建 |
| 任务重复执行 | ONESHOT_GRACE_SECONDS 太大 | 从 120 缩至 10 |
| 收不到 cron 输出 | DeepSeek 工具死循环 | prompt 第一行加硬指令"不要调工具" |

### 重复执行排查
一次性任务提醒了多次 = `cron/jobs.py` 中 `ONESHOT_GRACE_SECONDS=120` 导致 gateway 重启后任务被恢复执行。
修复：将 `ONESHOT_GRACE_SECONDS` 从 120 缩至 10，或在 `mark_job_run()` 中添加 `completed` 标记。

## 3. 审计与精简

### 何时审计
- 用户要求清理 cron jobs
- Token 费用过高，怀疑 cron 是原因
- 推送太多/太频繁

### 审计步骤
1. 列出所有活跃 job
2. 评估：频率是否合理？产出是否有新价值？错误率是否过高？
3. 高风险信号：每5-30分钟跑且产出全是"无变化"的感知引擎、一直报错的健康巡检

### 暂停操作
```bash
cronjob action=pause job_id=<id>
```
暂停不等于删除 — 可随时 `cronjob action=resume` 恢复。

## 4. 环境变量隔离

### 问题
cron jobs 用 `os.environ.update()` 设置临时变量但不清理，导致：
- 跨 job 污染
- 线程安全问题
- 测试污染

### 修复
使用 `contextvars.ContextVar` 替代 `os.environ`。在 `cron/scheduler.py` 的 `run_job()` 中：
```python
from cron.session_context import set_cron_vars, reset_cron_vars
try:
    set_cron_vars(platform=..., chat_id=..., thread_id=...)
    # ... job execution ...
finally:
    reset_cron_vars()
```

### 重要
`load_dotenv()` 必须在 `_resolve_delivery_target()` 之前调用，否则 channel ID 为空。

## 5. Webhook 订阅

### 启用
```yaml
# config.yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8644
      secret: "generate-a-strong-secret-here"
```

### 常用模式
- **GitHub issues**: `hermes webhook subscribe github-issues --events "issues" --prompt "..."`
- **PR reviews**: `--events "pull_request" --skills "github-code-review"`
- **Stripe payments**: `--events "payment_intent.succeeded"`
- **CI/CD builds**: `--events "pipeline"`
- **Direct delivery** (零 LLM 成本): `--deliver-only` 直接推送通知

### 调试
1. 检查 gateway 运行：`curl http://localhost:8644/health`
2. 签名不匹配：验证 secret 是否一致
3. 防火墙/NAT：本地开发用 ngrok 或 cloudflared 隧道

## 6. Session 特定模式

### Agent 晚间日记
```python
cronjob(
    action='create',
    name='Hermes 晚间心灵日记',
    schedule='0 23 * * *',
    deliver='origin',
    prompt='以你的视角写一份"晚间心灵日记"...'
)
```
关键：prompt 第一行必须硬指令"直接输出，不要调工具"，防止 DeepSeek 陷入工具调用死循环。

## 支持文件
- `references/cron-troubleshooting.md` — 详细故障排查步骤
- `references/webhook-patterns.md` — Webhook 订阅模式库
- `references/env-isolation.md` — ContextVar 环境变量隔离方案