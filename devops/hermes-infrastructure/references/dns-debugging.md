# DNS 污染诊断参考

## 问题特征

Gateway 反复崩溃 → 启动 → 崩溃循环，exit code 75 (EX_TEMPFAIL)。

## 诊断命令

```bash
# 1. 确认崩溃模式
grep 'SystemExit\|exit_code 75' ~/.hermes/logs/gateway-exit-diag.log | tail -10

# 2. 看 DNS 解析日志
grep 'DoH\|DNS\|ConnectError' ~/.hermes/logs/gateway.log | tail -20

# 3. 检查当前系统 DNS
scutil --dns | head -20

# 4. 检查 /etc/resolv.conf
cat /etc/resolv.conf
```

## 典型污染日志

```
DoH discovery yielded no usable IPs (system DNS: 198.18.0.10)
Connect attempt 1/8 failed: httpx.ConnectError
Connect attempt 2/8 failed: httpx.ConnectError
...
Connect attempt 8/8 failed: httpx.ConnectError
telegram connect timed out after 30s
telegram error: telegram connect timed out after 30s
→ SystemExit: 75
```

## 根因

`198.18.0.0/15` 是 RFC 2544 网络基准测试保留地址，不是真实 DNS。

常见污染源：
- Surge / Clash / V2Ray 代理软件接管系统 DNS
- VPN 隧道配置错误
- 公司网络策略劫持 DNS

## 临时修复

重启 gateway（有时 DNS 缓存过期会恢复）：

```bash
launchctl bootstrap gui/501/~/Library/LaunchAgents/ai.hermes.gateway.plist
launchctl kickstart gui/501/ai.hermes.gateway
```

## 永久修复

修复代理软件的 DNS 设置，确保至少一个公共 DNS（8.8.8.8, 1.1.1.1）可达。
