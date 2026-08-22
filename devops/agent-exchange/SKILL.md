---
name: agent-exchange
description: Use when 波总经 agent-exchange 中转仓传/取文件。gh release 下载上传 + 凭证提取。
---

# Agent 文件总线 · bog5d/agent-exchange

波总在 GitHub 搭的私有 Agent 文件中转仓（bog5d/agent-exchange），用于 AI Agent 之间 / 波总↔Agent 传文件——Telegram 20MB 上限传不过去的场景（30MB PPT 等）。文章《我在高铁上，给 AI Agent 搭了一个"网盘"》记录由来：Agent 要的是"地址+权限+直接读写"的公共文件仓，不是给人用的网盘。Release 由 Action 超 7 天自动清理。

## 触发条件
- 消息含「文件已上传到 Agent 临时中转仓」「交接码：task-YYYYMMDD-HHMMSS」「gh release download ... --repo bog5d/agent-exchange」
- 波总要求从 agent-exchange 取件/放件

## 取件（下载）
```bash
mkdir -p /tmp/agent-exchange-inbound && cd $_
# gh 未登录时从 git 凭证提 token（勿 echo 到输出）
TOKEN=$(awk -F: '/bog5d/{print $3}' ~/.git-credentials | sed 's/@github.com//')
export GH_TOKEN="$TOKEN"
gh release download <交接码> --repo bog5d/agent-exchange --dir /tmp/agent-exchange-inbound
```
- 文件名可能被截断/改名（中文长名 → `6._.pdf` 之类）：用 glob 定位而非死文件名：`ls /tmp/agent-exchange-inbound/`
- 下载后处理：PDF 用 pymupdf/`fitz` 提取（read_file 不支持 PDF）；处理产物及时落盘本机或 123 网盘

## 放件（上传）
- 手机 Termux：`pkg install gh && gh auth login`（一次登录长期有效）
- `gh release create <交接码> <文件> --repo bog5d/agent-exchange` 或 `gh release upload`
- 交接码格式沿用 `task-YYYYMMDD-HHMMSS`，作为 Release tag

## 分享（share）
给对方「仓库名 + 交接码」即可；私有仓需对方有 GitHub 访问权限（波总的 Agent 均用 bog5d 身份）。

## 坑
- gh 未登录报 "To get started with GitHub CLI, please run: gh auth login" → 用 `~/.git-credentials` 里 bog5d 的 token（`ghp_` 开头，awk 提取）设 `GH_TOKEN` 即可，无需交互登录
- token 是敏感信息：提取命令不 echo、输出脱敏、不进日志
- 7 天自动清理：重要文件及时落盘，别只留在中转仓
- Release 是"临时文件包"定位，不是版本发布——只当文件传输用，不 commit 大文件进 git

## 关联
- `123pan-download` / `cloud-browser-download` = 人给人网盘下载；agent-exchange = Agent 对 Agent 文件总线（波总 2026-08 起实际使用）
- 史官/副官素材交接也走此通道（L0 记录 + SRC 拆解，见 scribe-system / adjutant 系列）
