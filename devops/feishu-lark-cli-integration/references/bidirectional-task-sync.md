# 飞书任务 ↔ 副官系统 双向同步

## 架构 (v2, 2026-06-06 升级)

```
波总口述 "完成了" 
  → Hermes 更新 status.json (completed) + git push
  → sync_to_lark.py 阶段一：🧹 cleanup_completed()
    - 日历事件 → lark-cli calendar events delete（映射移除）
    - 飞书任务 → lark-cli task +complete（映射保留）
  → sync_feishu.py --direction to-feishu（逐任务确认）

波总飞书打勾 
  → cron 每15分钟 
  → sync_feishu.py --direction from-feishu 
  → 轮转逐查（每次3个，配额友好）
  → 检测飞书 completed_at 
  → 更新 status.json + git push 
  → 副官已同步 ✅
```

## 核心文件

| 文件 | 用途 |
|------|------|
| `scripts/sync_to_lark.py` | Hermes→飞书单向同步（创建+清理），新增 cleanup_completed() |
| `scripts/sync_feishu.py` | 双向同步引擎（逐任务查询，配额友好） |
| `feishu_task_mapping.json` | 副官 T0XX ↔ 飞书 GUID 映射 |
| `.feishu_checkpoint.json` | from-feishu 轮转检查点（新增） |
| cron job `a1582da9a8fa` | 每15分钟跑 sync_feishu.py --direction both |

## 映射表格式

```json
{
  "tasklist_guid": "b1df7ca1-e399-4466-bbda-7b9152cee418",
  "tasklist_url": "https://applink.feishu.cn/client/todo/task_list?guid=...",
  "mapping": {
    "T018": "42aaa3d3-323d-4a1d-821a-1e231888bab4",
    "T033": "5c4fb44e-c7ea-4e52-a498-ba4a47c29408"
  }
}
```

## 关键 Pitfall：is_completed 陷阱

飞书 API 中已完成任务的 `is_completed` 字段返回 `None` 而非 `True`。
同步脚本**必须**检查 `completed_at` 有无值来判断任务是否完成：

```python
# ❌ 错误
if task.get("is_completed"):
    mark_done()

# ✅ 正确
if task.get("completed_at"):
    mark_done()
```

## 关键 Pitfall：GUID 必须用完整 UUID

`lark-cli task +create` 返回的 GUID 是完整 UUID（36 字符，如 `42aaa3d3-323d-4a1d-821a-1e231888bab4`）。
`+search` 和 `+complete` 都要求完整 GUID。不能用截断的 8 字符前缀。
初始创建后应批量查询 `+search --query "T0XX"` 获取完整 GUID 填回映射表。

```bash
# 批量获取完整 GUID
for id in T018 T007 T014 T024 T027 T028 T029 T030 T031 T032 T033; do
  guid=$(lark-cli task +search --query "$id" --page-all 2>&1 | \
    python3 -c "import sys,json; items=json.load(sys.stdin)['data']['items']; print(items[0]['guid'] if items else 'NOTFOUND')")
  echo "$id = $guid"
done
```

## 关键 Pitfall：task +search 不支持 --data flag

`lark-cli task +search` 用 `--query`（关键词搜索）、`--completed`（筛选已完成）、`--page-all`（全量分页），**不支持** `--data` flag（会报 `unknown flag: --data`）。

## 关键 Pitfall：--page-all 配额消耗（2026-06 已验证）→ 已修复

`sync_feishu.py` 旧版 `sync_from_feishu()` 调用 `get_all_completed_tasks()` → `lark-cli task +search --completed --page-all`，每次翻页消耗 1 次 API 配额。飞书免费版 Base/文档/任务配额共享池，4-5 次即耗尽。

**2026-06-06 修复方案：逐任务查询 + 轮转检查点**

```python
# ❌ 旧方案（配额杀手，已删除）
completed = get_all_completed_tasks()  # --page-all 翻页

# ✅ 新方案：轮转逐查，配额友好（最多 3 次/轮）
cp = get_checkpoint()  # .feishu_checkpoint.json
start_idx = cp["last_index"] % len(pending_mapped)
for i in range(MAX_CHECKS):  # MAX_CHECKS = 3
    idx = (start_idx + i) % len(pending_mapped)
    t = pending_mapped[idx]
    task = get_feishu_task_status(mapping["mapping"][t["id"]])  # 1 次 API 调用
    if task.get("completed_at"):
        mark_completed(t)
cp["last_index"] = (start_idx + MAX_CHECKS) % len(pending_mapped)
save_checkpoint(cp)
```

**配额消耗对比：**

| 方案 | 每次调用 | 覆盖全部任务 |
|------|---------|-------------|
| 旧：`--page-all` 全量 | N 次翻页 + 1 次（一次性耗尽配额，后续全天失效） | 1 轮 |
| 新：轮转逐查 | 3 次（配额安全） | 22 任务需 ~8 轮（~2 小时@15min cron） |

**检查点文件 (`.feishu_checkpoint.json`)：**
```json
{"last_index": 3, "last_run": "2026-06-06T19:30:00+08:00"}
```
- 存储在 `hermes-adjutant/` 仓库内
- 每次运行后更新 `last_index` 为轮转结束位置
- 下次运行从该位置继续，确保所有任务逐步覆盖

## 关键 Pitfall：同步脚本重复创建任务（2026-06 真实事故）

### 事故

`sync_to_lark.py` 等同步路径每次遍历 `status.json` 时，因 `feishu_task_mapping.json` 未及时更新，无法识别已有任务 → 每次运行都重新创建 → 同一任务在飞书出现 3-8 份拷贝。

实际影响：T040（知乎账号）8 份、T041-T063 各 2-4 份，共约 60 份重复。

### 根因链

1. `sync_to_lark.py` 创建任务后未写回 `feishu_task_mapping.json`
2. 飞书 API 的 `--idempotency-key` 不可靠（不能防止重复）
3. 多个同步路径（`sync_to_lark.py`、`sync_feishu.py`、`feishu-sync-from-feishu.sh`、手动 `lark-cli`、`perception.py`）共享同一批任务，无去重锁
4. 映射文件仅 14 个条目（2026-05-24 冻结），新任务 T040-T074 全部缺失

### 修复

见 SKILL.md `重复任务清理 SOP` 章节。

### 防止复发

```python
# sync_to_lark.py 创建前必须检查映射
mapping = load_mapping()
if tid in mapping["mapping"]:
    print(f"📝 {tid} 已映射，跳过")
    return

guid = create_task(...)
mapping["mapping"][tid] = guid
save_mapping(mapping)  # 立即写回，铁律！
git_commit_push("update: feishu mapping {tid}")
```

## 防误匹配 + 映射 GUID 区分

映射中的 GUID 有两类，需区分处理：

| GUID 特征 | 类型 | 清理方式 |
|----------|------|---------|
| 带 `_0` 后缀（如 `c7acb36b-..._0`） | 飞书日历事件 | `calendar events delete` + 映射移除 |
| 纯 UUID（36字符，如 `47a14bbd-...`） | 飞书任务 | `task +complete` + 映射保留 |

方向二（飞书→副官）轮询时，仅处理纯 UUID 的飞书任务，跳过日历事件。日历事件不参与 from-feishu 回流。

同时，不能仅凭 GUID 匹配就标记完成——可能与其他飞书任务 GUID 冲突。必须验证 `summary` 包含任务 ID：

```python
if guid in feishu_completed:
    summary = feishu_completed[guid]
    if f"[{tid}]" in summary:  # 确认是我们的任务
        mark_completed(tid)
```

## perception.py 集成点

在 `PerceptionEngine.tick()` 的 ACT 步骤中，`git_change` 处理分支：

```python
if d["analysis"].get("completed_tasks"):
    run_feishu_sync_to()  # 触发 to-feishu 同步
```

`run_once()` 中，`git_has_new` 分支末尾：

```python
if git_has_new:
    results = run_executor_all()
    # ...
    run_feishu_sync_to()
```
