---
name: ai-file-delivery
description: 当需要把文件从本机交给其他 AI 读取时使用。通道选择、中文文件名坑、handoffs 仓库文件模式。
---

# AI 文件交付（AI↔AI 通道选择与坑位）

## 通道选择决策树

```
接收方是谁？
├── 其他 AI（Agent/远程会话）→ 用普通 GitHub 仓库文件（handoff 模式，见下）★ 波总指定首选
│   └── 备选：agent-exchange Release（仅当接收方能读 asset，默认不选）
├── 波总本人 → Telegram MEDIA（白名单目录）或 123 网盘链接
└── 外部人员 → 中转仓 release 或网盘（人工下载无 asset 类型问题）
```

## ★ 波总纪律（2026-08-30 指定）：给 AI 交件禁止走 Release 附件

**原因**：接收方 AI 无法读取 `application/octet-stream` 类型的 Release asset——下载下来是二进制垃圾或直接失败。Release 只适合人用浏览器下载。

**正确做法：普通仓库文件（handoff 模式）**

1. clone 目标私有仓（如 bog5d/agent-exchange）→ 新建 `handoffs/<task-id>/` 目录（可分子目录 reports/ agreements/ 等）
2. 按原文件名拷入，不压缩、不进 Release、不改写原件；附 `README_HANDOFF.md`（目录说明 + 未包含缺口清单 + 保密纪律）
3. commit + push（**推送会触发审批门禁，先向波总确认再执行**）
4. 回报四要素：仓库名、分支、每个文件的仓库相对路径、commit SHA
5. 接收方读取方式：
   - md/txt：raw URL `https://raw.githubusercontent.com/<owner>/<repo>/main/<path>`
   - 二进制（docx/pdf）：GitHub contents API，`encoding: base64` 解码

## 坑位

### 中文文件名被吞（实测 2026-08-30）
中文长名经 GitHub API 上传后 asset 名变成 `01_.md`、`6._.pdf` 之类——字符被吞。**上传/提交前先 `cp` 成 ASCII 文件名**（如 `linjianspace_inventory_01.md`），原件名对照表写进 README。

### token 提取
gh 未登录时从 `~/.git-credentials` 取 bog5d token 设 `GH_TOKEN`，勿 echo（见 agent-exchange skill 的凭证规则）。

### git push 审批门禁
push 外部仓库会触发审批门禁（前台需用户确认；后台会话直接被拦）。先在回复里说明要推送什么，拿到"允许"再执行。

### 大文件
Release 单文件上限约 2GB 但 AI 读不了；普通 git 文件建议 <50MB；超大文件走 123 网盘 + 链接。

## 关联技能
- `agent-exchange`（bundled）：中转仓取件/放件基础操作、凭证提取
- `handoff`：交接文档内容规范
- `media-file-delivery`：Telegram 通道的白名单机制
