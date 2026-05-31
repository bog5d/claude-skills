# 飞书任务 ↔ 副官系统 双向同步

## 架构

```
波总口述 "完成了" 
  → Hermes 更新 status.json (completed) + git push
  → perception.py 感知到 completed_tasks 
  → sync_feishu.py --direction to-feishu 
  → lark-cli task +complete → 飞书打勾 ✅

波总飞书打勾 
  → cron 每5分钟 
  → sync_feishu.py --direction from-feishu 
  → 检测飞书 completed_at 
  → 更新 status.json + git push 
  → 副官已同步 ✅
```

## 核心文件

| 文件 | 用途 |
|------|------|
| `scripts/sync_feishu.py` | 双向同步引擎 |
| `feishu_task_mapping.json` | 副官 T0XX ↔ 飞书 GUID 映射 |
| `scripts/perception.py` | 检测到 completed_tasks 时触发 to-feishu 同步 |
| cron job `a1582da9a8fa` | 每5分钟跑 from-feishu 方向 |

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

## 防误匹配

方向二（飞书→副官）轮询时，不能仅凭 GUID 匹配就标记完成——
可能与其他飞书任务 GUID 冲突。必须验证 `summary` 包含 `[T0XX]`：

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
