---
name: wechat-content-pipeline
description: "一步流：口述/初稿 → 直接出完整文章 → 排版配图 → 创建公众号草稿。一个入口，一次对话，一次确认。"
version: 2.0.0
author: Hermes Agent
platforms: [macos]
metadata:
  hermes:
    tags: [wechat, publishing, pipeline, content, writing, chinese, one-step]
    category: social-media
    related_skills: [content-research-writer, humanizer, wechat-quality-layout, wechat-publish-direct]
---

# 微信公众号一步流

**一个入口，一次对话，一次确认。** 波总口述/发初稿 → Hermes 全自动出完整文章 → 排版配图 → 创建草稿。中间不确认大纲、不确认分段、不确认标题——这些全是 AI 内部决策。

## 核心哲学

波总只需要做三件事：
1. **输入**：口述一堆想法，或发初稿
2. **看一眼**：收到完整文章后的确认（唯一停顿点）
3. **点发布**：去公众号后台点群发

**其余全是 AI 的活。** 不要在写作过程中反复问"大纲行不行""这一段行不行"。

## When to Use

任何内容发布场景自动走一步流：
- 口述/发零散想法 → 「帮我发公众号」
- 发初稿 → 「排版发布」
- 指定选题 → 「写一篇 XX 的文章发公众号」
- 任何提到「公众号」「发布」「发文章」的消息

## 一步流全貌

```
波总输入（口述 / 初稿 / 选题）
  │
  ▼  🟢 全自动（AI 内部决策，不中断用户）
┌─────────────────────────────────────────┐
│  Step 1: 搜资料（如需要）                 │
│  Step 2: 结构化 + 写完整初稿               │
│  Step 3: 去 AI 味 (humanizer)            │
│  Step 4: 生成 3 个标题备选 → 内部选定最佳    │
│  Step 5: 生成配图关键词 JSON               │
│  Step 6: 排版 (quality_layout.py)         │
│  Step 7: 替换配图占位符 (image_replace.py)  │
└─────────────────────────────────────────┘
  │
  ▼  🔴 唯一确认门
┌─────────────────────────────────────────┐
│  展示：完整文章预览 + 标题 + 摘要 + 封面种子  │
│  提问：「确认发布？」                       │
│    → 确认：创建草稿，返回 media_id         │
│    → 修改：按波总指示改                     │
│    → 取消：结束                            │
└─────────────────────────────────────────┘
  │
  ▼
🔚 去公众号后台 → 预览 → 群发
```

## 速度模式

| 模式 | 触发词 | 行为 |
|------|--------|------|
| **一步流**（默认） | 「发公众号」 | 口述→写→排→确认→发，只在最后停一次 |
| **极速** | 「不要停直接发」「全程自动」 | 跳过最后确认门，直接返回 media_id |
| **只写不发** | 「先写着看看」「快速写不发」 | 只出完整文章，不排版不发布 |
| **只排版发布** | 「排版发布」「这篇文章发一下」 | 已有定稿，直接排版→确认→发布 |

## Step 1-7 内部执行细则

### 触发识别

收到波总消息后，首先判断是否触发一步流：
- 包含「发」「公众号」「文章」「排版」「发布」等关键词 → 触发
- 波总发长篇文字/链接/文件 → 默认视为「要发的内容」→ 触发
- 明确说「先别发」「只是聊天」→ 不触发

### Step 1: 搜资料（条件触发）

**何时搜**：选题类（波总说「写一篇关于 XX 的文章」）→ 搜 3-5 个信息源。
**何时不搜**：口述个人经历/观点、已有完整初稿 → 跳过。

搜索后不展示结果，直接用于写作。

### Step 2: 结构化 + 写完整初稿

口述内容 → AI 自动：
- 去口语冗余（保留语气，去掉「那个」「就是说」等填充词）
- 理出主干逻辑（提炼 3-5 个核心观点）
- 扩写成完整文章（800-2000 字，视素材量而定）

**写作铁律**：
- 口语化，像在跟朋友聊天
- 不要新闻联播腔，不要「首先其次最后」
- 可以保留个人的犹豫和不确定
- 避免空洞升华和强行比喻
- 不展示大纲，不确认结构——直接出完整文章

### Step 3: 去 AI 味

走 `humanizer` Skill 处理：
- 替换 AI 高频词（「在当今」「值得注意的是」「综上所述」）
- 加口语转折（「说实话」「其实」「后来发现」）
- 保持原意不变

### Step 4: 标题生成

生成 3 个标题备选，内部按以下标准选定最佳：
- 有信息量，不说废话
- 制造悬念或反差
- ≤ 55 字节 UTF-8（中文约 18 字）
- 不用「重磅」「深度」「揭秘」等营销词

**不展示 3 个标题让波总选**——AI 直接选最佳，只展示最终标题。

### Step 5: 配图关键词

根据文章内容自动生成 `/tmp/article_images.json`：

```json
{
  "keywords": {
    "opening": ["english seed words", "matching content"],
    "chapter1": ["..."],
    "chapter2": ["..."],
    "ending": ["..."]
  },
  "captions": {
    "opening": "中文配图描述",
    "chapter1": "...",
    "chapter2": "...",
    "ending": "..."
  }
}
```

关键词用 picsum 英文种子词，caption 用中文描述。**必须和文章内容匹配**。

### Step 6-7: 排版 + 配图替换

```bash
cd ~/.hermes/skills/social-media/wechat-publish-direct/references

# Step 6: 排版
python3 quality_layout.py /tmp/article_final.md \
  --theme chinese \
  --images /tmp/article_images.json \
  --output /tmp/article_layout.html

# Step 7: 配图替换
python3 image_replace.py /tmp/article_layout.html \
  --output /tmp/article_styled.html
```

**错误处理**：排版失败 → 检查 quality_layout.py 路径和 JSON 格式 → 重试一次 → 仍失败则用纯文本 + 基础 CSS 降级。

### 确认门：展示预览

排版成功后，向波总展示：

```
## 📄 文章预览

**标题**：{title}（{字节数}/55）

**摘要**：{digest}

{完整文章正文，格式化展示}

---
**封面种子**：{cover_seed}
**配图种子**：{body_seeds}
**作者**：中本笨-BG
**预估字数**：{字数}
```

然后问：「**确认发布？**」

### 创建草稿

波总确认后执行：

```bash
cd ~/.hermes/skills/social-media/wechat-publish-direct/scripts

python3 publish_article.py \
  --article /tmp/article_styled.html \
  --cover-seed {自动提取} \
  --body-seeds {自动提取} \
  --author "中本笨-BG" \
  --title "{选定标题}" \
  --digest "{自动生成摘要}" \
  --output /tmp/final.html
```

### 交付

```
## ✅ 已创建草稿

**标题**：{title}
**草稿 ID**：{media_id}
**下一步**：打开公众号后台 → 草稿箱 → 预览 → 群发
```

---

## 预检清单（创建草稿前自动执行）

每项自动检查，失败则报告原因不继续：

```bash
# 1. Clash 规则
grep 'api.weixin.qq.com' ~/Library/Application\ Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml | grep -v DIRECT

# 2. 凭证
grep -E 'WECHAT_SECRET|DEEPSEEK_API_KEY' /Users/mac/.hermes/profiles/her-m2/.env | grep -v '^\*\*\*'

# 3. API 连通性（必须走 Clash 代理）
SECRET=$(grep WECHAT_SECRET /Users/mac/.hermes/profiles/her-m2/.env | head -1 | cut -d= -f2)
https_proxy=http://127.0.0.1:7897 curl -s \
  "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wx37940d296d26c91c&secret=${SECRET}" \
  --connect-timeout 5 | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'access_token' in d else d)"
```

---

## 错误处理速查

| 阶段 | 常见错误 | 处理 |
|------|---------|------|
| 排版 | quality_layout.py 路径不对 | 确认脚本在 wechat-publish-direct/references/ |
| 排版 | JSON 格式错误 | 检查 `/tmp/article_images.json` 语法 |
| 排版 | 配图 caption 不匹配 | `--images` JSON 未生效 → 重新传入 |
| 预检 | IP 不在白名单 | 检查 Clash 节点 IP → 加到微信后台 |
| 预检 | 凭证缺失 | 检查 her-m2/.env |
| 创建 | 40164 | IP 白名单 → 确认 Clash 代理生效 |
| 创建 | 45003 | 标题超 55 字节 → 截断 |
| 创建 | 45004 | 摘要超 115 字节 → 截断 |
| 创建 | 40007 | 封面图上传失败 → 换 seed 重试 |
| 创建 | 47001 | draft/update 格式错 → fallback draft/add |

---

## 关键限制

| 限制 | 值 | 说明 |
|------|-----|------|
| 标题 | 55 字节 UTF-8 | 中文 1 字≈3 字节，约 18 字 |
| 摘要 | 115 字节 UTF-8 | 提炼金句，禁用第一句话凑数 |
| 封面图 | 1MB 以下 jpg/png | picsum 占位图 |
| 正文图 | 1MB 以下 jpg/png | 每 400-600 字 1 张 |
| 作者 | 中本笨-BG | 固定值 |

---

## Pitfalls

1. **curl 必须走代理**：微信 API 连通性检查必须显式加 `https_proxy=http://127.0.0.1:7897`，直连 IP 不在白名单。
2. **quality_layout.py 路径**：在 `wechat-publish-direct/references/` 下，不在 `wechat-quality-layout/`。
3. **`--images` 不是 `--image-keywords`**：参数名是 `--images`。
4. **标题字节数**：`len(title.encode('utf-8'))` ≤ 55，不是字符数。
5. **不要反复确认**：波总的偏好是「一次对话出结果」。不要在写作过程中停下来问。如果对最终结果不满意他会告诉你改哪里。

---

## 与其他 Skill 的关系

| Skill | 负责 |
|-------|------|
| `content-research-writer` | Step 1-2 搜资料 + 写作 |
| `humanizer` | Step 3 去 AI 味 |
| `wechat-quality-layout` | Step 5-6 排版引擎 |
| `wechat-publish-direct` | 最终发布 + 预检 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 2.0.0 | 2026-07-22 | **一步流重构**：取消所有中间确认，Phase 1-6 压成一步，只留末尾一次确认门 |
| 1.0.0 | - | 初版：Phase 1-8 分段流程，每段可确认 |
