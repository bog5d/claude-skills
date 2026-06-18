# 微信公众号发布管线状态（2026-06-18 更新）

## 管线概览

```
波总文章 → DeepSeek排版 → 配图 → 微信draft/add → 返回media_id
```

## 当前状态（2026-06-18 实测）

| 组件 | 状态 | 说明 |
|------|------|------|
| 微信 access_token | ✅ 本地直连可用 | 用户手动提供 App Secret，IP 在白名单 |
| 微信素材上传 | ✅ 旧接口可用 | `/cgi-bin/material/add_material` 可成功上传 picsum 图片 |
| 微信草稿创建 | ✅ 已跑通 | POST draft/add 成功返回 media_id |
| DeepSeek API | ❌ 余额耗尽 | 主 key 402，排版阶段仍需解决 |
| 阿里云中继 SSH | ❌ 认证失效 | 无法自动获取凭证 |
| Unsplash/Pexels API | ❌ Key 失效 | 配图降级到 picsum.photos |

## 恢复阻塞项

### 1. DeepSeek API 余额
- 主 key: `sk-a9e82fef...847f`（402 Payment Required）
- 需要充值或换 provider
- **临时规避**：用户直接提供排版好的 HTML，Hermes 只做配图+草稿创建

### 2. 配图策略
- picsum.photos 可作为临时配图方案
- 用户可在公众号后台手动替换为高清图
- 下载 picsum 图片必须加 `curl -L`（302 重定向到 fastly）

## 已验证的参数

| 参数 | 值 |
|------|-----|
| APP_ID | wx37940d296d26c91c |
| 标题字节限制 | ≤55 UTF-8 bytes |
| 摘要字节限制 | ≤115 UTF-8 bytes |
| 配图频率 | 每400-600字1张 |
| 封面尺寸 | 640x427 |
| 素材上传接口 | `/cgi-bin/material/add_material`（旧接口） |
| 草稿创建接口 | `/cgi-bin/draft/add` |
