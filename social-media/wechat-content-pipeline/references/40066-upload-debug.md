# 微信素材上传 40066 排查记录

## 现象
上传 picsum 图片到微信素材库，反复返回 `{"errcode": 40066, "errmsg": "invalid url"}`。

## 排查过程

### 尝试1：Python urllib 直接 URL 上传
❌ 失败，微信不接受 URL 作为素材上传方式。

### 尝试2：Python http.client 手动构造 multipart
❌ 失败，40066。Content-Disposition 格式可能不完全符合微信要求。

### 尝试3：curl -F
❌ 失败，40066。即使是 curl -F 也返回相同错误。

### 根因分析
40066 "invalid url" 并非指图片 URL，而是微信对新接口 `material_material/add_material` 的 multipart 格式校验极其严格。该接口对 boundary、Content-Disposition、filename 参数的格式有精确要求。

## 解决方案

**使用旧接口 `/cgi-bin/material/add_material` 替代 `/cgi-bin/material/material_material/add_material`。**

旧接口对 multipart 格式容忍度更高，curl -F 和 Python http.client 均可成功上传。

##  picsum 图片注意事项

1. 下载时必须加 `-L` 跟随 302 重定向（picsum → fastly.picsum）
2. 不加 `-L` 会得到 0 字节文件，上传必然失败
3. picsum 图片尺寸通常为 640x427，符合微信封面比例

## 成功示例

```bash
# 下载（必须 -L）
curl -sL "https://picsum.photos/seed/wx01/640/427" -o /tmp/cover.jpg

# 上传（用旧接口）
curl -X POST "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=TOKEN&type=image" \
  -F "media=@/tmp/cover.jpg"
# 返回: {"media_id": "...", "url": "http://mmbiz.qpic.cn/..."}
```

## 相关错误码

| 错误码 | 含义 | 解决 |
|--------|------|------|
| 40066 | invalid url | 换旧接口 /material/add_material |
| 41030 | media type | 文件类型不支持 |
| 40007 | empty media_id | 草稿创建时 thumb_media_id 无效 |
| 45003 | title too long | 截断到 55 字节 |
| 45004 | digest too long | 截断到 115 字节 |
| 40164 | IP not whitelisted | 添加 IP 到公众号后台，等 30-60 分钟 |
