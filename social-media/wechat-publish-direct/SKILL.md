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

## 坑位与教训

1. **标题字节限制**：微信标题限制64**字节**（非字符），中文字UTF-8占3字节。必须 `len(title.encode()) <= 58` 保守截断。
2. **IP白名单**：生效需2-5分钟，错误码40164。
3. **access_token**：有效期7200秒，需缓存复用。
4. **正文不动**：波总原文不改逻辑和观点。
5. **封面图**：先上传素材获取media_id再创建草稿。
6. **图片占位符**：DeepSeek排版生成 `[IMAGE:keywords]`，用Unsplash搜索→上传微信→替换为`<img src="微信url">`。

## 执行脚本

完整脚本位于 `/tmp/wechat_publish.py`，流程：
1. DeepSeek排版（原样保留文字，插入图片占位符）
2. Unsplash下载→上传微信素材
3. 标题字节截断
4. 创建公众号草稿
