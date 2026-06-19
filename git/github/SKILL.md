---
name: github
description: Complete GitHub workflow — repo management, PR lifecycle, code review, issue triage, and auth setup. Covers the full git + GitHub API interaction surface.
---

# GitHub 工作流

## 1. 仓库管理
- 克隆、创建、fork 仓库
- 管理 remotes、branches、releases
- 认证：`gh auth login`（HTTPS token 或 SSH）

## 2. PR 工作流
- 分支 → 提交 → 打开 PR → CI → 合并
- 标准流程：`git checkout -b feature-x && git commit -m "..." && gh pr create`

## 3. 代码审查
- 使用 `gh pr diff` 查看变更
- 行内评论：`gh pr review --comment`
- 整体批准/请求更改：`gh pr review --approve` / `--reject`

## 4. Issue 管理
- 创建、triage、label、assign
- `gh issue create --title "..." --body "..."`
- `gh issue list --label "bug"` — 筛选

## 5. 常见陷阱
- PR 描述模板：确保包含变更摘要、测试说明、破坏性变更
- CI 失败：先检查具体失败步骤，再决定重试还是修复
- 合并冲突：`git fetch origin && git rebase origin/main`
- 权限：确认 gh CLI 有对应 repo 的 write 权限

## 支持文件
- `references/pr-review-checklist.md` — 代码审查清单
- `references/issue-triage-guide.md` — Issue 分级指南