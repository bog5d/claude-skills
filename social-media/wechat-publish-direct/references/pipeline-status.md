# 微信公众号发布管线状态（2026-06-17 更新）

## 管线概览

```
波总文章 → DeepSeek排版 → 配图 → 微信draft/add → 返回media_id
```

## 当前阻塞点

### 1. DeepSeek API 余额耗尽
- 主 key: `sk-a9e82fef...847f`（402 Payment Required）
- Agnes provider key 被 redact，无法使用
- Supxh provider 状态未知

### 2. 阿里云中继 SSH 认证失效
- 服务器 47.85.62.133:8787 可达（返回 `ok`）
- 但 SSH 密钥认证被拒（publickey 失败）
- 无法获取 `.env` 中的微信 App Secret

### 3. 微信 App Secret 缺失
- 不在本地 `.env` 文件中
- 只能通过中继服务器获取（但 SSH 已失效）
- 需要波总手动提供或在微信公众平台重新生成

## 恢复方案

### 方案 A：用户提供 App Secret（最快）
波总在 微信公众平台 → 开发 → 基本配置 获取 App Secret，提供后本地即可：
```bash
curl "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx37940d296d26c91c&secret={APP_SECRET}"
```

### 方案 B：修复中继 SSH
需要重新配置 SSH 密钥或密码认证。

### 方案 C：完全本地化（长期方案）
将 WeChat API key 存入本地 `.env`，不再依赖中继服务器。

## 已验证的参数

| 参数 | 值 |
|------|-----|
| APP_ID | wx37940d296d26c91c |
| 标题字节限制 | ≤55 UTF-8 bytes |
| 摘要字节限制 | ≤115 UTF-8 bytes |
| 配图频率 | 每400-600字1张 |
| Pexels API Key | i82kHS...LLaA |

## 配图备选

- **Pexels API**（首选）：免费，key 在 `.env` 中
- **Unsplash**（备选）：需 API key
- **picsum.photos**（兜底）：随机图，质量不可控
