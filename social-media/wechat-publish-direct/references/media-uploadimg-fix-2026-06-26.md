# media/uploadimg 架构修复（2026-06-26）

## 问题

`publish_article.py` 用 `material/add_material` 上传图片到素材库，然后在 draft/add 的 content HTML 中用 `<img data-uimg="media_id">` 引用。图片在微信后台不显示。

## 根因

**`data-uimg` 属性对 API 创建的草稿（`draft/add`）无效。** 它是微信编辑器前端的特性，不适用于服务端 API。

微信官方要求（微信开放社区确认）：**「涉及图片url必须来源『上传图文消息内的图片获取URL』接口获取」**。

## 正确的架构

```
正文图片：picsum → media/uploadimg → 微信 CDN URL → <img src="微信CDN_URL">
封面图：  picsum → material/add_material → media_id → thumb_media_id
```

### 两个接口对比

| 特征 | `material/add_material` | `media/uploadimg` |
|------|------------------------|-------------------|
| 用途 | 永久素材库（封面、模板） | 发表内容中的图片 |
| 返回值 | `media_id` | `url`（微信 CDN URL） |
| 占用素材名额（100000） | ✅ 占用 | ❌ 不占用 |
| 用于正文 `<img src>` | ❌ 不可用 | ✅ 必须用 |
| 用于 `thumb_media_id` | ✅ 可用 | ❌ 不可用 |
| 图片限制 | jpg/png, <1MB | jpg/png, <1MB |

## 代码变更

- **新增** `upload_image_for_content()` — 调 `POST /cgi-bin/media/uploadimg`，返回微信 CDN URL
- **修改** `publish_workflow()` — Step 3 拆为两条路径：
  1. 封面：`upload_to_wechat()` → `cover_media_id`
  2. 封面（正文）：`upload_image_for_content()` → `cover_wechat_url`
  3. 正文配图：`upload_image_for_content()` → `body_wechat_urls`
- **替换** `replace_picsum_with_media()` → `replace_picsum_with_wechat_urls()` — 不再注入 `data-uimg`，直接替换 `src` 属性值为微信 CDN URL
- **更新** 返回结构：返回 `cover_media_id` + `body_wechat_urls` 替代旧 `media_ids`

## 验证方法

```bash
python3 scripts/publish_article.py \
  --article /tmp/test_article.md \
  --cover-seed spring \
  --body-seeds flower,tree,kite \
  --socks5 127.0.0.1:1080

# 成功后登录微信公众平台 → 草稿箱 → 打开最新草稿 → 图片应正常显示
```

## 关联

- [微信开放社区：草稿箱接口限制](https://developers.weixin.qq.com/community/develop/doc/0004e4b5918f78e4354d9fd925fc00)
- [微信官方文档：上传发表内容中的图片](https://developers.weixin.qq.com/doc/subscription/api/notify/message/api_uploadimage.html)
