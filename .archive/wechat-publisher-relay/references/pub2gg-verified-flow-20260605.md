# pub2gg 验证链路 (2026-06-05)

## 基础设施状态

| 组件 | IP | 端口 | 状态 | 验证方式 |
|------|-----|------|------|---------|
| Relay (阿里云) | 47.85.62.133 | 8787 | ✅ 在线 | PM2 wx-publisher PID 1788339, uptime 6d |
| Relay SSH | 47.85.62.133 | 22 | ✅ | 密钥认证 `/Users/mac/.ssh/id_ed25519_alicloud` |
| FRP Server | 47.85.62.133 | 7000 | ✅ | frps running, token f48653aaa... |
| FRP Client (Mac) | localhost | — | ✅ | PID 1695, matched token |
| WordPress | 111.229.29.110 | 80 | ✅ | REST API reachable, Cloudflare front |
| WordPress DB | 111.229.29.110 | 3306 | ❌ | Not accessible from relay |
| 宝塔 Panel | 111.229.29.110 | 8888 | ❌ | Connection timeout |
| WP SSH | 111.229.29.110 | 22 | ❌ | Connection timeout |

## 端点验证

### GET /health
```bash
curl -s 47.85.62.133:8787/health
# → ok
```

### POST /publish
```
Status: ✅ Working
Input: 91-char Chinese test article
Output: DeepSeek formatted → 2 Unsplash images → WeChat draft
media_id: bQqYgPWs61_ROOqZBKIhz6WdY0rdg...
```

### POST /push_telegram
```
Status: ✅ Working (via SSH + source .env + curl localhost)
Input: {title, excerpt, wp_link, mp_name}
Output: msg_id=9 → @AgentToWest
Parse mode: HTML (NOT MarkdownV2)
```

## 全链路测试结果

```
1. /publish:     ✅ media_id created, 2 images auto-uploaded
2. /push_telegram: ✅ msg_id=9 to @AgentToWest
3. GitHub push:  ✅ 99e7b6b main -> main (hex-encoded PAT)
4. WP read:      ✅ Public REST API works
5. WP write:     ❌ WP_APP_PASS expired, admin login pwd changed
```

## 已知缺口

1. **WordPress → Relay webhook 不存在**：WP 发布后不会自动触发 pub2gg
2. **WordPress 凭证全部过期**：admin login `bqS2SBlY2AKG` 失效，app pass `boWm4uPKgEET` 失效
3. **无直接 VNC/SSH 到 WP 服务器**：需通过腾讯云 Lighthouse 控制台重置
