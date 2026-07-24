# publish_article.py 固化程序

## 概述

确定性发布管线，解耦"排版文字"和"插入配图"。每步有明确输入/输出，可独立验证。

## 路径

`scripts/publish_article.py`（569 行）

## 用法

```bash
python3 scripts/publish_article.py \
    --article /tmp/article_test.md \
    --cover-seed lantern \
    --body-seeds road,night,watermelon \
    --output /tmp/wechat_final.html
```

## 凭证来源

从 `~/.hermes/profiles/her-m2/.env` 读取：
- `DEEPSEEK_API_KEY`
- `WECHAT_APPID`（默认 `wx37940d296d26c91c`，可命令行覆盖）
- `WECHAT_SECRET`（**必须提供，无默认值**）

也可通过 `--appid` 和 `--secret` 命令行参数覆盖。

## 管线步骤

1. **DeepSeek 排版**：调用 DeepSeek API，生成微信格式 HTML（不含图片）
2. **图片上传**：从 picsum.photos 下载图片 → 上传微信素材库 → 获取 media_id
3. **HTML 注入**：将 `data-uimg` 占位符替换为微信素材 URL
4. **创建草稿**：POST `/cgi-bin/draft/add`，返回 media_id

## 已知限制

- 依赖 DeepSeek API（402 时失败）
- picsum 图片上传可能因格式被微信拒绝
- 新素材接口 `/material/material_material/add_material` 返回 40066，必须用旧接口 `/material/add_material`
