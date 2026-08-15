---
name: adjutant-system-ops
description: 副官系统写入后的验证与同步排障。git 报 nothing to add、飞书同步失败时使用。
category: user-patterns
---

# Adjutant System Ops — 写入验证与同步排障

## 触发条件
- 向副官系统写入任务 / 更新 status.json 后，`git add -A && git commit` 报 "nothing to add / nothing to commit / up-to-date"
- `sync_to_lark.py` / `sync_feishu.py` 报错
- 需要确认任务真的同步到了 GitHub 远端

## 核心事实：perception 引擎自动同步
- cron 每 5 分钟跑 `perception.py --once`（git sniff → pull → advisor → push）
- 手动写入 status.json 后，引擎可能已**抢先** commit+push（commit message 形如 `sync: 2026-08-15 16:50`）
- 因此手动 git 报 "nothing to add / up-to-date" 是**正常现象**，不是失败，也不是写入没生效

## 验证步骤（写入后必做，替代盲目手动 push）
```bash
cd ~/.hermes/adjutant/repo/hermes-adjutant
git show origin/main:status.json | grep -c "<TID>"    # 预期输出 1
git log origin/main --oneline -2                        # 看引擎是否已自动提交
```
- TID 出现在 origin/main 的 status.json 中 → 同步成功，无需手动 push
- 不在 → 手动 `git add -A && git commit -m "add: <描述>" && git push origin main`

## 飞书同步失败模式（sync_to_lark.py）
| 错误特征 | 含义 | 处理 |
|---------|------|------|
| `need_user_authorization (user: ou_...)` | 飞书授权过期 | 重跑无效；告知波总重新授权 lark-cli；GitHub 兜底 |
| 429 / 配额信息 | 免费版 4-5 次 API/天配额耗尽（0 点重置） | 等重置或 GitHub 兜底；勿用 `--page-all` |
- 两种情况下任务都不受影响（status.json 是单一事实源），但需向波总说明飞书侧有延迟
- 飞书打勾 ≠ 副官完成：from-feishu 是轮转轮询，回流有延迟

## 陷阱
- **macOS 无 GNU `timeout`**：`timeout 60 python3 ...` 报 `command not found`；直接跑 python3，或装 coreutils 用 `gtimeout`
- **execute_code 在审批/cron 模式被阻止**：DB 写入用 `terminal + python3 heredoc`（详见 adjutant-brain-dump 流程）
- **git pull/写库可能被审批拦截**：被拒后不要盲目重试同一条命令；先向波总确认是否放行，确认后原样重跑通常成功
- 不要靠 Hermes memory 判断任务状态——status.json 是单一事实源

## 关联技能
- `adjutant-boot`：启动协议（git pull → status.json → 汇报）
- `adjutant-brain-dump`：任务录入流程（DB + status.json 写入）
- 注意：以上技能为 bundled/受保护、不可直接 patch；本技能承载其运行时排障与验证知识
