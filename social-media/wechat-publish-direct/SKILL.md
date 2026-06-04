---
name: wechat-publish-direct
description: 波总发MD文章 → Hermes直接排版+配图+创建公众号草稿，跳过阿里云中继。当波总发送文章/文章链接要求"发布""发公众号""pub"时使用。
category: social-media
---

# 微信公众号直接发布（跳过中继）

## 凭证

```
APP_ID: wx37940d296d26c91c
APP_SECRET: 85c0...8d19
DeepSeek: sk-2426...e430
```

⚠️ 必须从阿里云服务器获取完整密钥：`ssh root@47.85.62.133 'cat /root/wx-publisher/.env'`

## 流程

### 1. 接收波总MD文章

波总发送原始MD文章。正文用波总原文不动。

### 2. 提取标题和摘要

从MD第一行提取标题（`# 标题`），生成摘要。

### 3. DeepSeek排版（可选）

调用DeepSeek API优化段落格式、生成金句摘要。流程同中继 `/publish` 端点的 formatArticle 逻辑。

API调用：
```bash
curl https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -d '{"model":"deepseek-chat","messages":[{"role":"system","content":"你是公众号排版专家..."},{"role":"user","content":"文章内容"}]}'
```

### 4. 配图

- 检查波总是否提供封面图
- 没有则用 `cover.jpg`（从服务器获取：`/root/wx-publisher/cover.jpg`）
- 或AI生成（comfyui/dalle）

### 5. 创建公众号草稿

获取 access_token：
```
GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=APP_ID&secret=APP_SECRET
```

创建草稿：
```
POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=TOKEN
{
  "articles": [{
    "title": "标题",
    "author": "中本笨-BG",
    "digest": "摘要",
    "content": "HTML正文",
    "content_source_url": "原文链接",
    "thumb_media_id": "封面图media_id",
    "need_open_comment": 0,
    "only_fans_can_comment": 0
  }]
}
```

### 6. 返回结果

返回 `media_id` 给波总 → 波总在公众号后台确认发送。

## 注意事项

- IP白名单生效需2-5分钟
- access_token有效期7200秒，需缓存
- 正文用波总原文，不改逻辑和观点
- 封面图需先上传获取media_id
