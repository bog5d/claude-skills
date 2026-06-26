# 微信公众号发布管线状态（2026-06-26 更新）

## 管线概览

```
波总文章 → Hermes参数层 → 确定性Markdown排版 → 配图下载 → media/uploadimg→微信CDN URL → draft/add
```

## 当前状态（2026-06-26 实测）

| 组件 | 状态 | 说明 |
|------|------|------|
| 微信 access_token via Clash 系统代理 | 🟢 通过 | `api.weixin.qq.com → 节点选择`，不再使用 `--socks5` |
| DeepSeek API | 🟢 正常 | `urllib.request` 直连（不走 SOCKS5） |
| 默认排版引擎 | 🟢 正常 | 默认 `--layout-provider deterministic`，AI 不生成最终 HTML |
| picsum 图片下载 | 🟢 正常 | `urllib.request` 自动跟 302 重定向 |
| 正文图片上传 media/uploadimg | 🟢 通过 | 返回微信 CDN URL（mmbiz.qpic.cn） |
| 封面图上传 material/add_material | 🟢 通过 | 返回 media_id 用于 thumb_media_id |
| 草稿创建 draft/add | 🟢 通过 | 直接使用微信 CDN URL 作为 `<img src>` |
| 图片渲染验证 | 🟡 待波总确认 | 已修复 CDN URL 完整替换逻辑；仍需在微信后台打开草稿确认图片显示 |
| 离线单元测试 | 🟢 通过 | `tests/test_publish_article.py` 覆盖 URL 替换、字节截断、解析和插入点 |
| CLI 干跑 | 🟢 通过 | `--dry-run` 可生成最终 HTML，不触发微信接口 |

## 架构变更记录

### 2026-06-26 架构修复：media/uploadimg

**问题**：`material/add_material` + `data-uimg` 对 draft/add 无效。
**修复**：正文图片改用 `media/uploadimg` 获取微信 CDN URL，直接作 `<img src>`。

详见 `references/media-uploadimg-fix-2026-06-26.md`。

## 已知限制

1. **配图源仍是 picsum**：seed 可复现，但图片语义与文章弱相关，且依赖外部随机图服务。
2. **Hermes 对话入口仍是技能说明 + CLI**：脚本内已有参数归一层，但 Hermes 外层还未强制使用 JSON schema 调用。
3. **图片渲染仍需人工验收**：草稿创建后必须在微信后台确认 `<img src="mmbiz.qpic.cn/...">` 实际显示。
