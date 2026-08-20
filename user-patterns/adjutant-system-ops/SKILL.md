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

## 认知演化 evolution.md 补登（拆解卡→索引，周期性欠账）

Cangjie_OBS_Notes 的 `知识库/认知演化/evolution.md` 常滞后于拆解卡（cron 日报会提示"自 X 日未增量登记"）。补登标准流程（2026-08-17 实测 55 条）：

1. **定位欠账区间**：读 evolution.md 找最后登记的 INS-YYYYMMDD-NNN 与最后章节日期；`ls 知识库/副官拆解/YYYY/MM/` 列出该日期后所有 SRC 卡
2. **批量提取"新增认知"段落**：
   ```bash
   awk '/新增认知|新增洞察|新认知/{found=1} found{print}' SRC-*.md
   ```
   只收"一句话认知"类条目；说话人身份确认（ai_inference）归实体索引不归 evolution
3. **编号顺排**：`INS-YYYYMMDD-NNN` 按登记日连续（如欠 8/12-8/16 的账 → INS-20260812-001 起），跨素材统一顺排
4. **插入位置**：新章节插在最后一个内容章节之后、**"## X、维护说明"之前**（patch 锚点用 `## 六、维护说明` 这类标题，替换为"新内容+原标题"）；维护说明必须是文件最后
5. **波总口述修正**：对话中波总对认知的确认/修正 → 追加到对应 INS 的"修正历史"，格式 `- 2026-08-17 波总确认：...`；旧表述不删
6. **校验提交**：`python3 系统检查/validate_repo.py` 报的密钥扫描类 ERROR（obs-wiki/raw/sources 历史文件）是**仓库既有问题**，与本次修改无关，看是否新增即可；然后 commit + push

## 陷阱
- **兄弟 AI 并发建任务（2026-08-20 实测）**：status.json/DB 可能在两次操作之间被其他 AI/cron 更新（本会话 T100 由兄弟代理先建，几分钟前 max ID 还是 T099）。对策：每次插入前重新交叉比对 DB 与 status.json 的 max ID（不能沿用上次会话/上次命令的结论），追加 tasks 数组前重读文件，push 后 `git pull` 复查远端。建卡/行程重复写会双行，追加行前先 grep 目标行是否已含要写的内容。
- **macOS 无 GNU `timeout`**：`timeout 60 python3 ...` 报 `command not found`；直接跑 python3，或装 coreutils 用 `gtimeout`
- **execute_code 在审批/cron 模式被阻止**：DB 写入用 `terminal + python3 heredoc`（详见 adjutant-brain-dump 流程）
- **git pull/写库可能被审批拦截**：被拒后不要盲目重试同一条命令；先向波总确认是否放行，确认后原样重跑通常成功
- 不要靠 Hermes memory 判断任务状态——status.json 是单一事实源

## 关联技能
- `adjutant-boot`：启动协议（git pull → status.json → 汇报）
- `adjutant-brain-dump`：任务录入流程（DB + status.json 写入）
- 注意：以上技能为 bundled/受保护、不可直接 patch；本技能承载其运行时排障与验证知识
