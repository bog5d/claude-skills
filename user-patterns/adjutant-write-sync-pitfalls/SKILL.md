---
name: adjutant-write-sync-pitfalls
description: Use when 副官系统录入/同步/行程冲突排查出错。运行时实测坑位。
---

# 副官录入与冲突排查运行时坑位（2026-09-07 实测）

> ⚠️ 本技能与 `adjutant-system-ops`（bundled，无法后台 patch）领域重叠——后台 curator 合并时可将本内容并入。

## sync.py 依赖链（重要修正）
`sync.py` 只读 `status.json` → 生成 `docs/tasks.md` + `docs/summary.json`。
**它不读 DB、也不反向写 status.json。** status.json 完全靠手动维护。

### 正确录入顺序
```
git pull
→ DB INSERT（列名 task_date/task_time，不是 date/time）
→ 手动改 status.json（重读文件追加，防兄弟 AI 并发覆盖；同时更新 total_pending）
→ python3 scripts/sync.py --push   ← 此时 docs 才包含新任务
→ git commit + push
```
若先跑 sync.py 再改 status.json → docs 漏新任务 + 多余 commit，需重跑一次 sync --push 修正。

## Schema 复核
- DB 列：`task_date` / `task_time` / `deadline` / `key_contacts`(JSON 字符串) / `category` / `claimed_by`
- status.json 字段：`date` / `time` —— **两套命名不同**
- 直接 SQL 用 `date`/`time` 报 `no such column: date`
- 写前核对：`sqlite3 ~/.hermes/adjutant/db/adjutant.db ".schema tasks"`

## 约见冲突排查工作流（外部邀约问"某天有没有空"）
1. SQL 查目标日期区间：
   ```sql
   SELECT id,title,task_date,task_time,deadline,priority FROM tasks
   WHERE status NOT IN ('completed','cancelled')
     AND (task_date BETWEEN 'a' AND 'b' OR deadline BETWEEN 'a' AND 'b')
   ORDER BY COALESCE(NULLIF(task_date,''),'9999');
   ```
2. 回复格式（波总偏好）：首行一句话结论（"X日无冲突，可约"）→ 近期盘面列表 → 远期相关任务提示
3. 对方时间未定时按"待确认"录入：task_date 留空，描述含原话出处；勿猜日期写死
4. 录入后照常 sync --push + git

## 常规陷阱
- **兄弟 AI 并发建任务**：每次插入前重新交叉比对 DB 与 status.json 的 max ID（`SELECT MAX(CAST(SUBSTR(id,2) AS INTEGER)) FROM tasks` + status.json 遍历取大者 +1）；追加 tasks 数组前重读文件；push 后 git pull 复查远端
- **git "nothing to add"**：perception 引擎每 5 分钟自动 commit+push（message 形如 `sync: 2026-09-07 11:02`），报 up-to-date 是正常现象，验证 TID 在 origin/main 即可
