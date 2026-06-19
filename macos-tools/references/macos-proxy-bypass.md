# macOS 系统代理劫持排查

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

# 3. 检查 Clash 配置 mode
cat ~/Library/Application\ Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml | grep '^mode:'
# mode 必须是 rule 而不是 global
```

## 解决方案

### 方案 A：Clash 规则直连（推荐）

在 `clash-verge.yaml` 中添加：
```yaml
rules:
- DOMAIN,目标域名,DIRECT
```

### 方案 B：临时关闭系统代理

```bash
networksetup -setwebproxystate "Wi-Fi" off
networksetup -setsecurewebproxystate "Wi-Fi" off
```

### 方案 C：通过 Clash Verge API 切换

```bash
curl --unix-socket /tmp/verge/verge-mihomo.sock \
  "http://localhost/proxies"
```

## 常见误区

| 误区 | 事实 |
|------|------|
| "设了 NO_PROXY 就能绕过" | 系统级代理在 TCP 层劫持，环境变量无效 |
| "用 raw socket 就不走代理" | macOS 上 socket 也经过 CFNetwork 代理栈 |
| "直连 IP 能绕过" | PF firewall RDR 规则在 TCP 层匹配，域名无关 |
