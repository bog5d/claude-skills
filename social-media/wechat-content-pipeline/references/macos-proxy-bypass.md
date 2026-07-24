# macOS 系统代理绕过 — Clash Verge / Surge 场景

## 问题

macOS 上的 **Clash Verge**（mihomo 内核）、**Surge**、**Shadowrocket** 等透明代理工具会在系统级别劫持所有出站 TCP 连接。即使：

- 设置了 `NO_PROXY` / `no_proxy` 环境变量
- 用 `http.client` 或 `socket` 原生连接
- 甚至直连 IP 地址

**全部无效** — 因为代理在 PF firewall / RDR 层面做 NAT 劫持，所有 TCP 层流量都被重定向到代理端口（通常 7897）。

## 诊断方法

```bash
# 1. 确认代理在运行
lsof -i :7897 -P -n 2>/dev/null | head -5
ps aux | grep -iE 'clash|surge|mihomo|shadow' | grep -v grep

# 2. 确认出口 IP 被劫持
curl -s ifconfig.me
# 如果返回的不是本机真实 IP → 走了代理

# 3. 检查 Clash 规则是否生效
cat ~/Library/Application\ Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml | grep -A2 'rules:'
# 注意：mode 必须是 rule 而不是 global
```

## 解决方案

### 方案 A：Clash 规则直连（推荐，无需改代码）

在 Clash Verge 配置文件中添加直连规则：

```yaml
rules:
- DOMAIN,api.weixin.qq.com,DIRECT
- DOMAIN-SUFFIX,example.com,DIRECT
```

**关键**：确保 mihomo 的 `mode` 是 `rule` 而不是 `global`。全局模式下所有流量都走代理，规则无效。

配置文件位置：
- Clash Verge: `~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml`
- mihomo 内核: `~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/mihomo.yaml`

### 方案 B：临时关闭系统代理

```bash
# 关闭 Wi-Fi 系统代理
networksetup -setwebproxystate "Wi-Fi" off
networksetup -setsecurewebproxystate "Wi-Fi" off
networksetup -setsocksfirewallproxystate "Wi-Fi" off

# 恢复
networksetup -setwebproxystate "Wi-Fi" on
networksetup -setsecurewebproxystate "Wi-Fi" on
```

⚠️ 这会断开所有联网程序的代理，包括浏览器。

### 方案 C：通过 Clash Verge API 切换

Clash Verge 暴露 Unix socket API：
```bash
curl --unix-socket /tmp/verge/verge-mihomo.sock \
  "http://localhost/proxies"
```

可以程序化切换 proxy group 或模式。

## 常见误区

| 误区 | 事实 |
|------|------|
| "设了 NO_PROXY 就能绕过" | 系统级代理在 TCP 层劫持，环境变量无效 |
| "用 raw socket 就不走代理" | macOS 上 socket 也经过 CFNetwork 代理栈 |
| "直连 IP 能绕过" | PF firewall RDR 规则在 TCP 层匹配，域名无关 |
| "curl 没问题所以 Python 也没问题" | curl 可能有不同的代理处理方式，不能类推 |

## 适用场景

- 微信公众号 API 调用（IP 白名单限制）
- 任何需要固定出口 IP 的服务
- 需要绕过代理测试连通性的场景
