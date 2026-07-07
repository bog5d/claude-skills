---
name: wechat-content-pipeline
description: "微信公众号一键全流程：选题→搜资料→写作→去AI味→标题→排版→配图→创建草稿。一句话从零到公众号后台。"
version: 1.0.0
author: Hermes Agent
platforms: [macos]
metadata:
  hermes:
    tags: [wechat, publishing, pipeline, content, writing, chinese]
    category: social-media
    related_skills: [content-research-writer, humanizer, wechat-quality-layout, wechat-publish-direct]
---

# 微信公众号一键全流程

**一句话从零到公众号草稿。** 把「写 + 排 + 发」三个 Skill 串成一条自动流水线。

## When to Use

触发条件：
- "帮我一键发公众号"
- "写一篇公众号文章并发布"
- "从写到发一条龙"
- "把这篇文章排版发布到公众号"

## 全流程一览

```
你发选题/文章
  │
  ▼
┌─────────────────────────────────┐
│  Phase 1-6: content-research-writer │
│  搜→大纲→写→验证→去AI味→标题      │
│  🔴 确认门: 大纲 / 标题            │
└─────────────────────────────────┘
  │ 定稿 (MD)
  ▼
┌─────────────────────────────────┐
│  Phase 7: wechat-quality-layout    │
│  中国风排版 + 配图占位             │
│  🟢 自动                          │
└─────────────────────────────────┘
  │ 排版 HTML
  ▼
┌─────────────────────────────────┐
│  Phase 8: wechat-publish-direct    │
│  预检→配图上传→封面→创建草稿       │
│  🔴 确认门: 创建草稿前             │
└─────────────────────────────────┘
  │ media_id
  ▼
🔚 去公众号后台 → 预览 → 群发
```

---

## Phase 1-6: 写作（content-research-writer）

**完全遵循 `content-research-writer` Skill 的流程。** 展开见该 Skill，此处仅保留关键确认点：

| Phase | 内容 | 模式 |
|-------|------|------|
| 1 | 搜资料 | 🟢 自动 |
| 2 | 出大纲 | 🔴 **确认** |
| 3 | 分段写作 | 🔴 **逐段确认** |
| 4 | 资料验证 | 🟢 自动（个人叙事类自然跳过） |
| 5 | 去AI味（humanizer） | 🟢 自动 |
| 6 | 标题诊断 | 🔴 **确认** |

**写作风格默认设定：**
- 口语化，像在跟朋友聊天
- 不要新闻联播腔
- 不要「首先其次最后」
- 可以有个人的犹豫和不确定
- 避免空洞升华和强行比喻

---

## Phase 7: 排版 + 配图关键词（quality_layout.py）

**🟢 自动执行，不中断。**

步骤：

### 7.1 生成配图关键词 JSON

**每篇文章创建一个 `/tmp/article_images.json`**，定义自己的配图关键词和中文 caption：

```json
{
  "keywords": {
    "chapter1": ["ai agent automation", "robot writing desk"],
    "chapter2": ["linked chain connection", "workflow gears"],
    "chapter3": ["checklist progress", "milestone markers"],
    "chapter4": ["speed dial control", "three paths fork"],
    "ending": ["open source sharing", "collaboration teamwork"]
  },
  "captions": {
    "chapter1": "工作台示意",
    "chapter2": "Skill 串联管线",
    "chapter3": "从搜到发全流程",
    "chapter4": "三种速度模式",
    "ending": "开源，拿走直接用"
  }
}
```

关键词取 picsum 英文种子词，caption 取中文描述。**必须和文章内容匹配**——不要用默认的农村/风景关键词。

### 7.2 调用排版引擎

```bash
# 注意：quality_layout.py 在 wechat-publish-direct/references/ 下
cd ~/.hermes/skills/social-media/wechat-publish-direct/references

python3 quality_layout.py /tmp/article_final.md \
  --theme chinese \
  --images /tmp/article_images.json \
  --output /tmp/article_layout.html
```

**关键参数**：`--images`（不是 `--image-keywords`），传入 JSON 覆盖默认配图关键词和 caption。

### 7.3 替换配图占位符

```bash
python3 image_replace.py /tmp/article_layout.html \
  --output /tmp/article_styled.html
```

### 7.4 验证配图

检查生成的 HTML 中的 caption 是否与内容匹配。如果出现「院坝里的夏夜」「路旁的碎西瓜」等不相关 caption → `--images` JSON 未生效，回去检查。

---

## Phase 8: 创建草稿（wechat-publish-direct）

### 8.1 预检 【🟢 自动】

按顺序检查三项，任一项失败 → 停止并报告原因：

```bash
# 1. Clash 规则
grep 'api.weixin.qq.com' ~/Library/Application\ Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml | grep -v DIRECT

# 2. 凭证
grep -E 'WECHAT_SECRET|DEEPSEEK_API_KEY' /Users/mac/.hermes/profiles/her-m2/.env | grep -v '^\*\*\*'

# 3. API 连通性（⚠️ 必须走 Clash 代理，本地 IP 不在微信白名单）
SECRET=$(grep WECHAT_SECRET /Users/mac/.hermes/profiles/her-m2/.env | head -1 | cut -d= -f2)
https_proxy=http://127.0.0.1:7897 curl -s \
  "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx37940d296d26c91c&secret=${SECRET}" \
  --connect-timeout 5 | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'access_token' in d else d)"
```

预检通过 → 展示三盏绿灯，进入下一步。
预检失败 → 报告具体是哪一项，不继续。

### 8.2 收集发布参数

从定稿中提取（或向用户确认）：

| 参数 | 说明 | 限制 |
|------|------|------|
| `--title` | 文章标题（Phase 6 已选定） | ≤55 字节 UTF-8 |
| `--digest` | 摘要（提炼金句，禁用第一句话凑数） | ≤115 字节 UTF-8 |
| `--author` | 作者名 | 默认"王波" |
| `--cover-seed` | 封面图种子词（描述整体氛围） | 英文关键词 |
| `--body-seeds` | 正文配图种子词（逗号分隔，3-5 个） | 英文关键词 |

**封面图和配图种子词由 AI 自动从文章内容提取**，展示给用户但不中断。

### 8.3 干跑验证 【🟢 自动】

```bash
cd ~/.hermes/profiles/her-m2/skills/social-media/wechat-publish-direct/scripts

python3 publish_article.py \
  --article /tmp/article_styled.html \
  --cover-seed {自动提取} \
  --body-seeds {自动提取} \
  --author "王波" \
  --title "{Phase 6 选定的标题}" \
  --digest "{自动生成摘要}" \
  --dry-run \
  --output /tmp/final.html
```

干跑成功 → 展示「排版验证通过，准备创建草稿」。
干跑失败 → 报告错误，不继续。

### 8.4 创建草稿 🔴 【确认门】

展示最终参数摘要：

```
## 📤 即将创建公众号草稿

| 项目 | 内容 |
|------|------|
| 标题 | {title}（{字节数}/55） |
| 摘要 | {digest} |
| 作者 | 王波 |
| 封面种子 | {cover_seed} |
| 配图种子 | {body_seeds} |
| 预检 | ✅ Clash ✅ 凭证 ✅ API |
| 干跑 | ✅ 通过 |
```

**停下来问：「创建草稿？」**

用户确认后执行：

```bash
python3 publish_article.py \
  --article /tmp/article_styled.html \
  --cover-seed {cover_seed} \
  --body-seeds {body_seeds} \
  --author "王波" \
  --title "{title}" \
  --digest "{digest}" \
  --output /tmp/final.html
```

成功 → 返回 media_id。
失败 → 根据错误码速查表定位问题。

---

## 交付

```
## ✅ 全流程完成

**标题**：{title}
**字数**：{字数}
**草稿 ID**：{media_id}
**下一步**：打开公众号后台 → 草稿箱 → 预览 → 群发

📄 排版文件：/tmp/final.html
```

---

## Pitfalls

1. **Phase 7 排版脚本路径**：`quality_layout.py` 和 `image_replace.py` 在 `wechat-publish-direct/references/` 下，**不在** `wechat-quality-layout/references/`。那个目录不存在。
2. **`--images` 不是 `--image-keywords`**：参数名是 `--images`，传入 JSON 覆盖配图关键词。
3. **Phase 8 输入格式**：如果传 HTML 给 `publish_article.py`，它自动检测并走直通模式（跳过 Markdown 渲染）。但如果是 Markdown → 走专属渲染——不会发生 HTML 转义。
4. **配图 caption 验证**：生成后在 HTML 中搜索「院坝」「碎西瓜」「灶台」——如果出现 → `--images` JSON 没生效。
5. **预检走代理**：微信 API 连通性检查必须走 Clash 代理（`https_proxy=http://127.0.0.1:7897`），直连 IP 不在白名单。
6. **旧草稿清理**：同名草稿会触发 `draft/update`（可能失败），建议每次改 cover-seed 确保创建新草稿。

| 你说 | 行为 |
|------|------|
| 「一键发公众号：{选题}」 | 只在大纲和创建草稿前确认，其余全自动 |
| 「全部自动发：{选题}」 | 跳过所有确认门，只在最后创建草稿前停一次 |
| 「快速写不发」 | 只走 Phase 1-6，停在第 6 阶段，不排版不发布 |
| 「排版发布」 | 已有定稿，直接走 Phase 7-8 |
| 「干跑看看」 | Phase 1-8.3，不创建草稿 |

---

## 错误处理

| 阶段 | 常见错误 | 处理 |
|------|---------|------|
| 预检 | IP 不在白名单 | 检查 Clash 节点 IP → 加到微信后台 |
| 预检 | 凭证缺失 | 检查 .env 文件 |
| 干跑 | 输出空 | 检查 article 路径 |
| 创建 | 40164 | IP 白名单问题 — 检查 Clash 规则 + `https_proxy` |
| 创建 | 45003 | 标题超 64 字节 — 截断到 55 字节 |
| 创建 | 45004 | 摘要超 120 字节 — 截断到 115 字节 |
| 创建 | 40005/40009 | 图片格式/大小问题 |
| 创建 | 40007 | 封面图上传失败 |
| 创建 | 47001 | draft/update 格式错误 → 自动 fallback 到 draft/add 创建新草稿 |
| 创建 | HTML 渲染为代码 | `publish_article.py` 已加 HTML 直通检测：输入是 HTML 自动跳过 Markdown 渲染 |

---

## 关键限制

| 限制 | 值 | 说明 |
|------|-----|------|
| 标题 | 55 字节 UTF-8 | 中文 1 字≈3 字节，约 18 字 |
| 摘要 | 115 字节 UTF-8 | 提炼金句，不用第一句话 |
| 封面图 | 1MB 以下 jpg/png | picsum 占位图 |
| 正文图 | 1MB 以下 jpg/png | 每 400-600 字 1 张 |
| 配图源 | picsum.photos | 随机风景照，非 AI 生成 |

---

---

## Pitfalls

1. **curl 默认不走系统代理** —— Phase 8.1 API 连通性测试必须显式加 `https_proxy=http://127.0.0.1:7897`，否则走本地 IP 会被微信 40164 拒绝。Clash 节点 IP（89.208.247.51）才是白名单里的。
2. **quality_layout.py 不在 wechat-quality-layout** —— 脚本实际位于 `wechat-publish-direct/references/`，路径依赖此目录。
3. **标题字节数不是字符数** —— `len(title.encode('utf-8'))` ≤ 55，中文 1 字≈3 字节，约 18 字封顶。
4. **API 预检失败不要跳过** —— 预检失败直接创建草稿会报 40164，且草稿可能残留。

---

## 与其他 Skill 的关系

本 Skill 是编排层，具体执行委托给：

| Skill | 负责 |
|-------|------|
| `content-research-writer` | Phase 1-6 写作流程 |
| `humanizer` | Phase 5 去AI味 |
| `wechat-quality-layout` | Phase 7 排版 |
| `wechat-publish-direct` | Phase 8 发布 |

## 支持文件

| 文件 | 用途 |
|------|------|
| `templates/image_keywords.json` | 配图关键词 JSON 模板，复制后按文章修改 |
| `references/robustness-fixes-2026-07-07.md` | 2026-07-07 全流程测试发现的 4 个 Bug 及修复记录 |
