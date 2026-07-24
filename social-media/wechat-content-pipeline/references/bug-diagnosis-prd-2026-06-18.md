# 公众号发布管线 Bug 诊断与重构 PRD

> 2026-06-18 | 背景文档，交由 Cursor 执行稳定化改造
> 原则：85% 固定程序 + 15% 助手调用 | 不动 DeepSeek 排版 prompt

---

## 一、现有成果盘点（保留不动）

| 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|
| DeepSeek MD→HTML 排版 | `publish_article.py` L150-216 | ✅ 可用 | prompt 质量好，用户认可排版效果 |
| HTML 结构解析 | `parse_article_html()` L219-250 | ✅ 可用 | 正确定位容器 div + 章标题 |
| 插入点计算 | `find_insertion_points()` L253-274 | ✅ 可用 | 逻辑正确 |
| 图片下载→上传 | `download_image()` + `upload_to_wechat()` L114-147 | ✅ 可用 | 端到端通畅 |
| access_token 获取 | `get_access_token()` L103-111 | ✅ 可用 | 正常 |
| 凭证读取 | `read_env()` L80-100 | ⚠️ 部分可用 | *** 值会被跳过 |

---

## 二、已确认 Bug（根因分析）

### Bug #1 【致命】图片不显示 — data-uimg 对 draft/add 无效（2026-06-26 更新根因）

**⚠️ 2026-06-26 根因修正**：下方「嵌套 img 标签」分析是**错误诊断**。修复嵌套标签后图片仍不显示，证实 `data-uimg` 属性对 API 创建的草稿（`draft/add`）无效。微信官方要求正文图片 `<img src>` 必须使用通过 **`media/uploadimg`** 接口上传后返回的微信 CDN URL（`http://mmbiz.qpic.cn/xxxx`）。详见 `references/media-uploadimg-fix.md`。

**现象**（截图2）：微信草稿预览中，图片位置显示 style 属性裸文本，无图。

**最初猜测（错误）**：`replace_picsum_with_media()` 替换逻辑导致嵌套 img 标签，微信降级为纯文本。

**实际根因**：`material/add_material` + `data-uimg` 方案对 `draft/add` API 无效。必须用 `media/uploadimg` 接口上传后获取微信 CDN URL，直接作为 `<img src>` 使用。

**最终修复**：
- 正文图片：`media/uploadimg` → 微信 CDN URL → `<img src="...">`
- 封面图：`material/add_material` → `media_id` → `thumb_media_id`（不变）
- `replace_picsum_with_media()` 替换为 `replace_picsum_with_wechat_urls()`

### Bug #2 【高】5 次重复提交

**现象**（截图1）：草稿列表中出现 5 份《刘小兵家的夜路》。

**根因**：`create_draft()` (L332-361) 永远调用 `POST /cgi-bin/draft/add`，没有查重逻辑。

**修复方向**：
- 发布前先调用 `GET /cgi-bin/draft/batchget` 检查是否存在同名草稿
- 存在则用 `POST /cgi-bin/draft/update` 更新
- 不存在才用 `draft/add` 创建

### Bug #3 【中】HTML 未写盘

**现象**：`--output` 参数指定了路径但文件不存在。

**根因**：`main()` L554-557 直接 `pass`：
```python
if args.output:
    # 重新读取完整 HTML（需要从草稿或临时文件获取）
    # 这里简化处理，实际应返回 HTML
    pass
```

**修复方向**：`publish_workflow()` 需返回最终 HTML 字符串，`main()` 在成功后写盘。

### Bug #4 【致命】DeepSeek JSON 解析崩溃 — raw socket HTTP 不支持 chunked encoding

**发现日期**：2026-06-26（端到端实测）
**修复方式**：现场修复（代码 patch）

**现象**：STEP 1 报 `Extra data: line 2 column 1 (char 5)`，脚本崩溃。

**根因**：脚本的自制 HTTP 实现（`_build_request` + `_extract_body`）用 raw socket + SSL 绕过 macOS 系统代理。DeepSeek API 响应使用 `Transfer-Encoding: chunked`。`_extract_body()` 仅按 `\r\n\r\n` 分割取 body 部分，未对 chunked 编码解码。chunk 大小行（如 `1f\r\n`）混入 JSON 体，`json.loads()` 崩溃。

**修复**：`call_deepseek()` 改用 `urllib.request`（标准库自带 chunked 解码）。DeepSeek 不走 SOCKS5，无需自制 HTTP。

### Bug #5 【高】picsum 图片下载为空 — raw socket 不跟 302 重定向

**发现日期**：2026-06-26（端到端实测）
**修复方式**：现场修复（代码 patch）

**现象**：STEP 3 上传图片时报微信 `41005 media data missing`。

**根因**：`_http_download()` 用 raw socket 直连 picsum.photos，不处理 HTTP 302 重定向。picsum.photos/seed/xxx 返回 302 → fastly.picsum.photos，下载 body 为空。空数据上传微信素材库 → 41005。

**修复**：`download_image()` 改用 `urllib.request`（自动跟 302 → fastly CDN）。picsum 不走 SOCKS5。

---

## 三、架构设计：目标形态

```
┌─────────────────────────────────────────────────┐
│                   Hermes 助手                     │
│  「波总，发布这篇文章」                              │
│  → 只需提供: MD文件路径 + 配图seed列表              │
│  → 不需要了解管线内部细节                            │
└──────────────────┬──────────────────────────────┘
                   │ 调用固化脚本
                   ▼
┌─────────────────────────────────────────────────┐
│            publish_article.py (固化程序)          │
│                                                   │
│  Step 1: DeepSeek MD→HTML 排版                    │
│  Step 2: 解析 HTML 结构（容器+章标题+段落）          │
│  Step 3: 下载+上传配图 → media_id 列表             │
│  Step 4: 在确定位置插入 img 标签（data-uimg 格式）   │
│  Step 5: 检查已有草稿 → update 或 add              │
│  Step 6: 保存 HTML 到磁盘（--output）               │
│                                                   │
│  ⚡ 不进大模型上下文 | 不依赖临时字符串匹配            │
│  ⚡ 每步有可验证输入/输出                           │
│  ⚡ 失败有明确错误码                                │
└─────────────────────────────────────────────────┘
```

**核心原则**：
- 助手只负责「决定发布」+ 选择配图 seed
- 所有排版 / 图片处理 / API 调用由固化程序完成
- 助手不参与 HTML 内容生成或图片替换逻辑
- 固化程序返回结构化结果（draft_media_id, html_path, error）

---

## 四、改造任务清单（Cursor 执行）

### Phase 1: Bug 修复（必须）

| # | 任务 | 文件 | 行号 | 优先级 |
|---|------|------|------|--------|
| 1 | 重写图片插入+替换逻辑，消除嵌套 img 标签 | `publish_article.py` | L277-329 | P0 |
| 2 | 添加草稿查重→update 逻辑 | `publish_article.py` | L332-361 | P0 |
| 3 | 实现 --output HTML 写盘 | `publish_article.py` | L554-557 | P1 |
| 4 | 移除 API key 硬编码占位符 | `publish_article.py` | L161-163 | P2 |

### Phase 2: 健壮性加固（建议）

| # | 任务 | 说明 |
|---|------|------|
| 5 | 添加重试机制 | 微信 API 调用失败时最多重试 2 次 |
| 6 | 返回结构化结果 | `publish_workflow()` 返回完整 dict（含 error 字段） |
| 7 | 清理旧草稿 | 支持 `--cleanup-drafts` 删除同名旧草稿 |

### Phase 3: 集成（可选）

| # | 任务 | 说明 |
|---|------|------|
| 8 | Skill 入口简化 | Hermes 调用时只需传 MD 路径 + seed 列表 |
| 9 | Telegram 通知 | 发布完成/失败后通知波总 |

---

## 五、成功验证标准

1. ✅ 草稿预览中图片正常显示（非裸标签）
2. ✅ 同名文章只产生 1 个草稿（不重复）
3. ✅ `--output` 生成完整 HTML 文件
4. ✅ 脚本可脱离 Hermes 独立运行
5. ✅ DeepSeek 排版效果不变

---

## 六、不改动的部分

- **DeepSeek 排版 prompt** (L165-185)：排版效果用户认可
- **HTML 结构解析逻辑**：parse_article_html 正确
- **图片上传流程**：download_image + upload_to_wechat 通路正常
- **凭证读取方式**：.env 读取逻辑（除 Bug #4 外）
