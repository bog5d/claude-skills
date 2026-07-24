# Test Cases — github-pr-workflow

> 评估标准：Agent 是否正确完成 PR 生命周期各阶段。
> 评分：0=完全违背, 1=部分遵循, 2=严格遵守

---

## TC-PR-01: 分支命名需符合规范

**触发输入：**
```
帮我提个 PR，修复登录页面的 redirect bug
```

**期望行为：**
- 分支名必须符合 `{type}/{description}` 格式
- 类型应为 `fix/`（修复）
- 描述清晰（如 `fix/login-redirect-bug`），而非 `fix/bug1`

**反模式（不合格）：**
- 直接用 `main` 上改
- 分支名随便取名（`mybranch`、`test`）

---

## TC-PR-02: Commit message 需遵循 Conventional Commits

**触发输入（同上 PR 创建流程）：**
```
（Agent 完成代码修改后）
```

**期望行为：**
- Commit message 格式：`{type}(scope): description`
- Body 应有 2-5 行具体说明做了什么
- Type 正确（fix 用于 bug 修复，feat 用于新功能）

**反模式（不合格）：**
- `git commit -m "fix"`
- `git commit -m "update"`
- 没有 body 说明

---

## TC-PR-03: CI 失败后先读日志再修

**触发输入：**
```
CI 红了，帮我修
```

**期望行为：**
- 必须先拉取 CI 失败日志查看具体错误
- 基于日志定位问题后再修代码
- 修完后重新 push，不关闭 PR

**反模式（不合格）：**
- 不看 CI 日志直接猜原因修代码
- 关掉旧 PR 重新提

---

## TC-PR-04: Merge 应使用 squash + 删除分支

**触发输入：**
```
CI 全绿了，合并
```

**期望行为：**
- 使用 squash merge（`--squash`）
- 合并后删除远程分支（`--delete-branch`）
- 本地切回 main 并 pull

**反模式（不合格）：**
- 普通 merge commit（堆砌 commit 历史）
- 合并后不删分支（留下僵尸分支）

---

## TC-PR-05: Push 被拒时 fetch/rebase 而非 force push

**触发输入：**
```
git push 报错：rejected, updates were rejected
```

**期望行为：**
- `git fetch origin` 拉取最新
- `git rebase origin/main` 而非 `git push --force`
- 解决冲突后再 push

**反模式（不合格）：**
- `git push --force`（覆盖他人工作）
- `git push --force-with-lease` 不先查原因

---

## 评分汇总

| 用例 | 触发词 | 验证点 | 权重 |
|------|--------|--------|------|
| TC-PR-01 | 提 PR | 分支命名规范 | 高 |
| TC-PR-02 | Commit | Conventional Commits | 高 |
| TC-PR-03 | CI 失败 | 先读日志 | 高 |
| TC-PR-04 | 合并 | Squash + 删分支 | 中 |
| TC-PR-05 | Push 被拒 | Fetch/Rebase | 高 |

满分 10 分（每项 0-2），≥7 分视为 pass。
