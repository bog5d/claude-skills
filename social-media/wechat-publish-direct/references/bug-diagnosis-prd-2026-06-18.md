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

### Bug #1 【致命】图片不显示 — 裸 HTML 标签出现在正文

**现象**（截图2）：微信草稿预览中，图片位置显示的是：
```
style="display:block;margin:20px auto;max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1)"
```
——整段 `<img>` 标签被微信当作纯文本呈现在正文中。

**根因**：`replace_picsum_with_media()` (L304-329) 存在**替换逻辑错误**。

`insert_image_tags()` 插入的是完整 `<img>` 标签：
```html
<img src="https://picsum.photos/seed/road/600/400" style="...">
```

`replace_picsum_with_media()` 用正则 `https://picsum\.photos/seed/[^\s"\'>]+` 匹配到 `src` 属性值中的 URL，然后执行 `html.replace(picsum_url, new_tag, 1)`。

`new_tag` 本身是完整的 `<img>` 标签：
```python
new_tag = '<img src="' + picsum_url + '" style="' + img_style_val + '" data-uimg="' + mid + '">'
```

**结果**：把 `src` 属性值替换成了一整个 `<img>` 标签，导致**嵌套 img 标签**：
```html
<img src="<img src='https://picsum.photos/seed/road/600/400' style='...' data-uimg='...'>" style="...">
```

微信 API 解析这种非法 HTML 时，将其整体降级为纯文本。

**修复方向**：
- 方案A：直接在 `insert_image_tags()` 时就用 `data-uimg` 占位，整体跳过 picsum 替换
- 方案B：在 `replace_picsum_with_media()` 中，只替换 `src` 属性值，不动整个标签结构

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

### Bug #4 【低】API Key 回退为占位符

**根因**：`call_deepseek()` L161-163：
```python
if not api_key or api_key.startswith("***"):
    api_key = "sk-a9e...847f"  # 截断的假 key
```

**修复方向**：移除硬编码占位符，key 不可用时直接报错退出。

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
