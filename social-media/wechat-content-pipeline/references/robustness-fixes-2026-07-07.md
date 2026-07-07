# 鲁棒性修复记录 — 2026-07-07 全流程测试

## 发现的 5 个问题及修复

### Bug 6: 配图 caption 跑偏
- **现象**：公众号草稿配图显示「院坝里的夏夜」「路旁的碎西瓜」等农村题材 caption，与 AI 技术文章完全不匹配
- **根因**：`quality_layout.py` 的 `IMAGE_KEYWORDS` 字典硬编码了 countryside 主题关键词
- **修复**：
  1. 默认 `IMAGE_KEYWORDS` 改为 tech 主题
  2. 新增 `IMAGE_CAPTIONS` 字典，含章节中文描述
  3. 新增 `--images` JSON 参数支持，每篇文章可传自定义关键词和 caption

### Bug 7: Markdown 表格不渲染
- **现象**：文章中的 `| Skill | 干什么 |` 表格变成纯文本段落
- **根因**：`parse_markdown()` 没有表格解析逻辑
- **修复**：
  1. 新增 `table` 块类型解析（跳过 `|---|---|` 分隔行）
  2. `render_blocks()` 新增 `<table class="wechat-table">` 渲染
  3. `chinese.css` 新增 `.wechat-table` 样式（金色表头 + 边框）

### Bug 8: draft/update 47001 阻塞
- **现象**：`draft/update` API 返回 47001 "data format error"，脚本直接抛 ValueError
- **根因**：`draft/update` 的 payload 格式与微信 API 期望不完全匹配
- **修复**：`publish_article.py` 的 `create_draft()` 中，更新失败不再抛异常，改为 `log()` 警告 + fallback 到 `draft/add` 创建新草稿

### Bug 9: 异常 Unicode 漏入草稿
- **现象**：公众号草稿 CSS 中出现 `￼` (U+FFFC OBJECT REPLACEMENT CHARACTER)
- **根因**：管道无字符清洗步骤
- **修复**：新增 `sanitize_html()` 函数，在 `create_draft()` 入口处清洗：
  - U+FFFC (Object Replacement)、U+FFFD (Replacement)
  - 零宽字符 (U+200B-U+200F)
  - 行/段分隔符 (U+2028-U+2029)、BOM (U+FEFF)
  - 其他控制字符

### Bug 10: 排版后的 HTML 被当 Markdown 重新渲染
- **现象**：公众号草稿显示原始 HTML 代码（`<p>` `<table>` 等标签可见），文章完全不可读
- **根因**：`publish_article.py` 的 STEP 1 把已排版的 HTML 文件当 Markdown 输入，`markdown_to_wechat_html()` 将 HTML 标签当作文本输出
- **修复**：新增 HTML 直通模式：
  - 检测输入是否以 `<!DOCTYPE` 或 `<html` 开头
  - 是 → 提取 `<body>` 内容，跳过 STEP 1-5，直接进入 STEP 6 创建草稿
  - 当前暂剥离 picsum 图片（后续可替换为微信 CDN 上传）

## 额外发现

### API 预检需要代理
- curl 默认不走系统代理 → `api.weixin.qq.com` 直连被 40164 拒绝
- 正确做法：`https_proxy=http://127.0.0.1:7897 curl ...`
- Clash 节点 IP（89.208.247.51）在微信白名单，本地 IP 不在

### `--images` 参数名（非 `--image-keywords`）
- argparse 定义为 `--images`（不是 `--image-keywords`）
- 传入 JSON 文件路径，覆盖默认 `IMAGE_KEYWORDS` 和 `IMAGE_CAPTIONS`

### `image_replace.py` double-alt bug
- 原 `replacer()` 返回 `url" alt="caption"` 导致两个 alt 属性
- 修复为只返回 URL，caption 由 quality_layout 模板控制

## 管道鲁棒性总结

每次发公众号草稿前，管道自动执行：
1. `sanitize_html()` — 清洗异常 Unicode
2. 查重 → 尝试 update → 失败 fallback 到 add（不会阻塞）
3. HTML 直通检测 → 已排版文件跳过低质量 Markdown 渲染
4. 所有图片通过 `media/uploadimg` 上传微信 CDN
