---
name: git-precheck
description: 开发前 Git 前置检查 — 防多 AI 并行开发冲突。每次改代码前先 fetch + diff 检查远端是否有新提交。
category: devops
---

# Git Pre-Check 前置检查

## 触发条件
- 任何涉及代码修改的指令（改代码、修Bug、重构、增功能）
- 每次开发对话开始时
- push 失败时

## 步骤

### 1. Fetch + Diff
```bash
cd <repo_path>
git fetch origin master
```

### 2. 检查三个方向
```bash
# 本地领先远端（我有未推的 commit）
git log origin/master..HEAD --oneline

# 远端领先本地（别人推了新代码）
git log HEAD..origin/master --oneline

# 文件级冲突风险（两者都改了哪些文件）
git diff --stat HEAD..origin/master
```

### 3. 决策树
| 状态 | 动作 |
|------|------|
| 本地领先，远端无新 → 无冲突 | 直接开发 |
| 远端领先本地 → 需要合并 | `git pull --rebase origin master` |
| 双方都有新 commit → 需 rebase | 先 stash → `git pull --rebase` → pop，解决冲突后重跑测试 |
| 远端改了同一文件 → ⚠️ 高风险 | 先读远端版本，确保不覆盖对方工作 |

### 4. 有冲突时的安全流程
1. `git stash` 暂存本地改动
2. `git pull --rebase origin master`
3. 如有冲突，手动解决，优先保留双方新增内容
4. `git stash pop`
5. 重跑测试确认 `pytest tests/ -q` 全绿
6. 再 push

## 验证
检查 `git log --oneline -5` 确认合并后的历史连续无分叉。

---

## ⚠️ 版本号冲突（多 AI 并行独有）

当两个 AI 都用了同一版本号（如各发一个 v0.6.1）：

### CHANGELOG.md 合并四步法
Rebase 时 CHANGELOG.md 冲突是最常见的——两个 AI 都在「Unreleased」位置插了新版本段。

1. **打开冲突文件** — `git status` 找到 CHANGELOG.md，用编辑器打开
2. **保留双方版本段** — 删除 `<<<<<<<` / `=======` / `>>>>>>>` 标记，两段都保留，远端在上、本地在下
3. **本地版本号 +1** — 远端已占用了某版本号（如 0.6.1），本地的重命名为 0.6.2
4. **同步 AGENTS.md** — 版本号表格和顶部状态行都要更新
5. `git add CHANGELOG.md AGENTS.md && git rebase --continue`

### 验证
```bash
# 确保两个版本段都在
grep -c "^## \[0\.6\." CHANGELOG.md
# 确认 AGENTS.md 版本号是最新的
grep "当前状态" AGENTS.md
```

### 常见陷阱
- **只更新了 AGENTS.md 忘记 CHANGELOG**：用 `git show <commit> --stat` 反查，若只动了 AGENTS.md 补写 CHANGELOG 条目
- **版本号跳号**：0.6.0 → 0.6.3（跳过 0.6.1/0.6.2 被远端占用）属于正常，在 CHANGELOG 补录被跳过的远端版本即可

---

## macOS Push 认证问题

macOS keychain 在非交互终端不可用。两种方案：

**方案 A（推荐）：credential helper 内联**
```bash
git -c credential.helper= \
    -c credential.helper='!f() { echo "username=token"; echo "password=<PAT>"; }; f' \
    push origin master
```

**方案 B：URL 内嵌 token（可能超时）**
```bash
git push "https://<PAT>@github.com/owner/repo.git" master
```

方案 B 在网关/远程环境可能超时，优先用方案 A。
