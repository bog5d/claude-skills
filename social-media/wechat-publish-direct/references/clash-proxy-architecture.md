# Clash 代理 + 微信公众号 API 架构

> 2026-06-26 | 从 raw socket + SOCKS5 隧道迁移到此架构

## 架构演变历史

### Phase 1: 直接加 IP 白名单（放弃）
- 本机宽带 IP 是动态的（C-G NAT / ISP 轮换），几分钟一变
- 微信 IP 白名单只能加单个 IP，每次变化都要重新添加
- 且白名单添加后需 30-60 分钟才生效，跟不上变化

### Phase 2: SOCKS5 隧道 → 阿里云（放弃）
- SSH 隧道到阿里云服务器 `47.85.62.133`（固定公网 IP）
- 通过阿里云固定 IP 访问微信 API
- 本机用 raw socket + SSL 绕过系统代理
- **问题**：依赖阿里云中继、阿里云 DNS 坏过、维护成本高

### Phase 3（当前）: Clash 代理节点
- Mac Mini 常年开着 Clash Verge（系统代理 `127.0.0.1:7897`）
- 把 `api.weixin.qq.com` 的 Clash 规则从 DIRECT 改成「节点选择」
- 代理节点有固定 IP，加一次微信白名单永久有效
- `publish_article.py` 全部用 `urllib.request` 标准库，自动走系统代理

## Clash 规则文件位置

```
~Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml
```

## 规则变更

```diff
- - DOMAIN,api.weixin.qq.com,DIRECT
+ - DOMAIN,api.weixin.qq.com,节点选择
```

## Clash API（通过 Unix socket）

```bash
# 查询当前代理节点
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/proxies

# 重载配置
curl -s -X PUT --unix-socket /tmp/verge/verge-mihomo.sock \
  http://localhost/configs?force=true \
  -H "Content-Type: application/json" \
  -d '{"path": ""}'
```

## 当前节点与出口 IP

| 项目 | 值 |
|------|-----|
| 当前代理节点 | CDN-无敌复活节点 |
| 出口 IP | 89.208.247.51 |
| 微信白名单状态 | ✅ 已加 |

## 排查 IP 白名单问题

```bash
# 查看本机真实 IP 和代理出口 IP 的区别
echo "直接: $(curl -s --noproxy '*' https://api.ip.sb/ip)"
echo "代理: $(https_proxy=http://127.0.0.1:7897 curl -s https://api.ip.sb/ip)"

# 微信看到的是哪个 IP？
curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=XXX&secret=YYY"
# 40164 错误里会显示微信看到的 IP
```
