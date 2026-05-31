# Gateway Revival Procedure

## 何时使用
当用户报告 gateway 死了、不响应、或者进程列表中缺失时。

## 快速诊断

```bash
# 查看所有 gateway 进程
ps aux | grep "hermes_cli.main gateway" | grep -v grep

# 查看各 profile 最新日志
for p in her-m2 default english-tutor; do
  echo "=== $p ==="
  tail -1 ~/.hermes/profiles/$p/logs/gateway.log 2>/dev/null || echo "无日志"
done
```

## 复活命令（一键）

```bash
# her-m2
/Users/mac/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main --profile her-m2 gateway run --replace &

# default (副官) — 注意它的 PID 在 ~/.hermes/gateway.pid 而非 profiles/default/
/Users/mac/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main --profile default gateway run --replace &

# english-tutor
/Users/mac/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main --profile english-tutor gateway run --replace &
```

**关键**：必须用 `--replace` 参数，否则旧 PID 文件残留会导致 "Gateway already running" 错误。

## 常见死因

| 症状 | 原因 | 预防 |
|------|------|------|
| english-tutor 自杀退出 | signal-initiated shutdown（可能是 launchd 或 cron 触发） | 检查 launchd plist 的 KeepAlive 设置 |
| default 无进程 | 从未配置为持久运行 | 添加 launchd/cron 保活 |
| 所有 gateway 同时死 | 系统重启或 Python 版本切换 | defibrillator 监控 |
| DNS 污染 crash | `198.18.0.10` 等拦截 DNS 导致 API 调用超时 | 已修复，但偶发 |

## 验证复活成功

复活后检查三件事：
1. 进程在 `ps aux` 中可见
2. 日志有新行（最近 1 分钟内）
3. Telegram 能收到消息

```bash
# 快速三合一检查
ps aux | grep "hermes.*gateway" | grep -v grep | wc -l | xargs echo "进程数:"
for p in her-m2 default english-tutor; do
  log="~/.hermes/profiles/$p/logs/gateway.log"
  [ "$p" = "default" ] && log="~/.hermes/logs/gateway.log"
  echo -n "$p: "
  find $(dirname $log) -name gateway.log -mmin -3 2>/dev/null | wc -l | xargs echo "最近日志:"
done
```

## defibrillator 状态

her-m2 有 defibrillator 进程保活（PID 60904），default 和 english-tutor 没有。
如需添加：编辑 her-m2 的 defibrillator 脚本，添加对其他 profile 的监控。
