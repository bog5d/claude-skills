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

## Absorbed Sibling Skills

This umbrella absorbed the following GitHub-specific skills as labeled subsections below. Each covered one aspect of the GitHub workflow; they now live together under this class-level skill.

| Former Skill | Now In |
|-------------|--------|
| github-auth | §GitHub 认证设置 |
| github-code-review | §代码审查 |
| github-issues | §Issue 管理 |
| github-pr-workflow | §PR 工作流 |
| github-repo-management | §仓库管理 |
| git-precheck | `references/git-precheck.md` |

---

## § GitHub 认证设置（absorbed from github-auth）

Two main auth paths: **git-only** (HTTPS tokens or SSH) and **gh CLI** (rich API access).

### Detection
```bash
gh auth status 2>/dev/null || echo "gh not authenticated"
```

### Method 1: Git-only (HTTPS with PAT)
```bash
git config --global credential.helper store
# Use PAT as password, never GitHub password
git ls-remote https://github.com/<user>/<repo>.git
```

### Method 2: SSH Key
```bash
ssh-keygen -t ed25519 -C "email@example.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub  # Add to GitHub Settings → SSH Keys
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

### Method 3: gh CLI
```bash
gh auth login  # Interactive browser
# or token-based:
echo "TOKEN" | gh auth login --with-token
gh auth setup-git
```

### Token Redaction Trap
Hermes redacts `ghp_...` tokens from terminal output. Use `execute_code` sandbox to clone:
```python
from hermes_tools import terminal
terminal(f"GIT_TERMINAL_PROMPT=0 git clone https://{token}@github.com/owner/repo.git ~/target")
# Then clean: git remote set-url origin https://github.com/owner/repo.git
```

---

## § 代码审查（absorbed from github-code-review）

### Local Changes Review (Pre-Push)
```bash
git diff main...HEAD --stat
git diff main...HEAD
# Check for issues:
git diff main...HEAD | grep -n "TODO\|FIXME\|debugger"
git diff main...HEAD | grep -in "password\|secret\|token.*="
```

### Review Output Format
```
## Code Review Summary
### Critical — [file:line] issue with suggestion
### Warnings — [file:line] concern
### Suggestions — minor improvements
### Looks Good — positive notes
```

### PR Review (Remote)
```bash
gh pr view 123
gh pr diff 123
gh pr checkout 123  # Check out locally for full review
```

### Inline Comments & Formal Review
```bash
# Submit review with inline comments
HEAD_SHA=$(gh pr view 123 --json headRefOid --jq '.headRefOid')
gh api repos/o/r/pulls/123/reviews --method POST \
  -f body="Review summary" \
  -f event="COMMENT|APPROVE|REQUEST_CHANGES" \
  -f comments='[{"path":"src/auth.py","line":45,"body":"Use parameterized queries."}]'
```

### Review Checklist
Systematically check: Correctness, Security (no secrets/SQLi/XSS), Code Quality (DRY, naming, SRP), Testing, Performance, Documentation.

---

## § Issue 管理（absorbed from github-issues）

### Common Operations
```bash
# Create
gh issue create --title "Bug: ..." --body "## Description\n..." --label "bug"

# View/List
gh issue list --state open --label "bug" --assignee @me
gh issue view 42

# Manage
gh issue edit 42 --add-label "priority:high" --add-assignee username
gh issue close 42 --reason "completed"
gh issue comment 42 --body "Working on a fix."
```

### Templates
Bug reports: Description → Steps → Expected → Actual → Environment
Feature requests: Description → Motivation → Solution → Alternatives

### Linking to PRs
Body keywords `Closes #42`, `Fixes #42`, `Resolves #42` auto-close on merge.

---

## § PR 工作流（absorbed from github-pr-workflow）

### Full PR Lifecycle
```bash
# 1. Branch
git checkout -b feat/description

# 2. Code & Commit
git add <files>
git commit -m "feat: short description\n\nLonger explanation."

# 3. Push & PR
git push -u origin HEAD
gh pr create --title "feat: ..." --body "## Summary\n..." --label "enhancement"

# 4. CI Monitoring
gh pr checks --watch

# 5. Merge
gh pr merge --squash --delete-branch
```

### Auto-Fix CI Loop
1. Check CI status → identify failures
2. Read logs → understand error
3. Fix with `patch`/`write_file`
4. `git commit -m "fix: ..." && git push`
5. Re-check, repeat up to 3 times

### Merge Methods
- `--squash` (cleanest for feature branches)
- `--rebase` (linear history)
- `--merge` (merge commit)

---

## § 仓库管理（absorbed from github-repo-management）

### Operations
```bash
# Clone
git clone https://github.com/owner/repo.git
gh repo clone owner/repo -- --depth 1

# Create
gh repo create my-project --public --clone
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{"name":"my-project","private":false}'

# Fork
gh repo fork owner/repo --clone

# Releases
gh release create v1.0.0 --title "v1.0.0" --generate-notes

# Secrets
gh secret set API_KEY --body "your-secret-value"

# Workflows
gh workflow list
gh run list --limit 10
gh run rerun <RUN_ID> --failed
```

### Branch Protection
```json
{
  "required_status_checks": {"strict": true, "contexts": ["ci/test"]},
  "required_pull_request_reviews": {"required_approving_review_count": 1}
}
```