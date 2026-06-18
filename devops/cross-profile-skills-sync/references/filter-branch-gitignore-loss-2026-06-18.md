# filter-branch 丢失 .gitignore — 2026-06-18 案例

## 现象
`git filter-branch` 重写 326 个提交后，`.gitignore` 在工作树中完全消失。

## 根因
`.gitignore` 曾在历史中的某个提交被删除或修改，filter-branch 按最终状态还原工作树。

## 修复
```bash
cd /Users/mac/.claude/skills
ls .gitignore 2>&1 || cp templates/gitignore-credentials.txt .gitignore
# 验证
cat .gitignore
```

## 预防
filter-branch 后**立即**检查 `.gitignore`，不要等到 commit 时才发现问题。
