# 微信公众号发布管线状态（2026-06-26 更新）

## 管线概览

```
波总文章 → DeepSeek排版 → 配图下载 → media/uploadimg→微信CDN URL → draft/add
```

## 当前状态（2026-06-26 实测）

| 组件 | 状态 | 说明 |
|------|------|------|
| 微信 access_token via SOCKS5 | 🟢 通过 | `--socks5 127.0.0.1:1080` → 47.85.62.133 固定 IP → 微信 API |
| DeepSeek API | 🟢 正常 | `urllib.request` 直连（不走 SOCKS5） |
| picsum 图片下载 | 🟢 正常 | `urllib.request` 自动跟 302 重定向 |
| 正文图片上传 media/uploadimg | 🟢 通过 | 返回微信 CDN URL（mmbiz.qpic.cn） |
| 封面图上传 material/add_material | 🟢 通过 | 返回 media_id 用于 thumb_media_id |
| 草稿创建 draft/add | 🟢 通过 | 直接使用微信 CDN URL 作为 `<img src>` |
| 图片渲染验证 | 🟡 待波总确认 | 需在微信后台打开草稿确认图片显示 |

## 架构变更记录

### 2026-06-26 架构修复：media/uploadimg

**问题**：`material/add_material` + `data-uimg` 对 draft/add 无效。
**修复**：正文图片改用 `media/uploadimg` 获取微信 CDN URL，直接作 `<img src>`。

详见 `references/media-uploadimg-fix-2026-06-26.md`。

## 已知限制

1. **章标题正则不匹配「一、内容」格式**：`find_insertion_points()` regex `[一二三四五六七八九十]` 只匹配单字，不匹配带顿号的格式。临时规避：修改 regex 为 `[一二三四五六七八九十][、]?`。
2. **SOCKS5 隧道需要 live**：隧道掉线时微信 API 因 IP 白名单不可达。检查命令：`ps aux | grep "ssh.*1080" | grep -v grep`。
