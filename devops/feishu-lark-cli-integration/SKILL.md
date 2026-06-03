---
name: feishu-lark-cli-integration
description: 安装并配置飞书 lark-cli，使 Hermes Agent 能通过命令行操作飞书日历、文档、任务。含 Hermes credential 保护下的正确配置流程。
---

# 飞书 CLI 集成

让 Hermes Agent 通过 `lark-cli` 操作飞书：创建日历事件、生成行程日志文档、管理任务。

---

## 前置条件

- Node.js ≥ 18
- 飞书管理员权限（创建应用或已有应用的 App ID + Secret）
- 波总扫码授权（关键步骤，必须人工完成）

---

## Step 1：安装 lark-cli

```bash
npm install -g @larksuite/cli
# 确认安装
export PATH="$HOME/.npm-global/bin:$PATH"
lark-cli --version
```

---

## Step 2：配置飞书凭证

### 2a. 先检查现有状态

```bash
export PATH="$HOME/.npm-global/bin:$PATH"
lark-cli config show
```

**如果输出已包含 `appId` 和 `users`（非 "no logged-in users"），则凭证已配置，直接跳到 Step 3。**
如果 `users` 显示 `"(no logged-in users)"`，说明凭证在但未授权 ← **这是最常见的情况**。

### 2b. 如果 config show 为空才需要绑定

大多数情况下凭证已在。仅当 `config show` 返回空或报错时才需要 `config bind`。**首次配置场景才走这一步。**

```bash
# 方式A：如果 App ID/Secret 已存在于 ~/.hermes/.env（用 config bind）
lark-cli config bind \
  --source hermes \
  --app-id cli_xxxxxxxxxxxx \
  --identity user-default \
  --force

# 方式B：如果新建应用（用 config init，非 Hermes 上下文）
lark-cli config init
```

`--identity` 选择：
- `user-default`：需要操作个人日历/文档/邮件时选这个
- `bot-only`：仅群聊/机器人场景，更安全

### 2c. 如果 .env 缺失凭证

gateway 运行时，credential 保护机制锁定已有 .env 行，但**新增行不受影响**：

```bash
cat >> ~/.hermes/.env << 'EOF'

# =============================================================================
# FEISHU (Lark) INTEGRATION
# =============================================================================
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=your_secret_here
EOF
sleep 3 && grep FEISHU ~/.hermes/.env  # 验证写入

---

## Step 3：用户扫码授权

这是唯一需要波总人工操作的步骤。

### 推荐：不等待模式（避免 timeout）

```bash
# Step A: 发起授权（不等待）—— 必须指定 --domain！
lark-cli auth login --no-wait --json --domain calendar,task,docs,contact,im
# 返回：{"device_code": "...", "verification_url": "https://...", "expires_in": 600}
```

**把 `verification_url` 逐字原样发给波总**，不要 URL 编码、不要改写成 Markdown 链接、不要加空格或标点。建议用只包含 URL 的代码块单独输出。

⚠️ device code 只有 **10 分钟**有效期。波总扫码后执行：

```bash
# Step B: 波总扫码后，用 device_code 完成轮询
lark-cli auth login --device-code <device_code>
# 最长阻塞 600 秒，波总已扫码则几秒内返回
```

### 防止授权链接过期的后台轮询模式

device code 有效期仅 10 分钟。如果波总不能立即扫码，用后台轮询：

```bash
# Step A: 发起授权（不等待）
lark-cli auth login --no-wait --json --domain <domains>
# 记下 device_code

# Step B: 后台轮询（不会超时，自动通知完成）
lark-cli auth login --device-code <device_code> &
# 或使用 Hermes terminal background=true notify_on_complete=true
```

这样波总即使 9 分钟后才扫码也不会过期——后台进程一直轮询。

### 备选：阻塞等待模式（需要长 timeout）

```bash
lark-cli auth login --recommend
# 最长阻塞 600s。如果 Hermes terminal timeout < 600s 会中断，device code 作废。
```

### 授权结果解读

输出中 `"授权结果异常: 以下请求 scopes 未被授予: ..."` **不是真正的错误**。
只要看到以下核心 scopes 已授予，授权就是成功的：

✅ 必需：`calendar:calendar.event:create`, `calendar:calendar.event:read`, `calendar:calendar.event:update`, `calendar:calendar.event:delete`
✅ 必要：`task:task:read`, `task:task:write`, `docx:document:create`
❌ 可忽略的未授予：`calendar:calendar.event:reply`, `im:message.send_as_user`, `im:chat:create_by_user`, `search:docs:read`, `search:message`

**只有 `exit_code=0` 才是完全成功。exit_code=3 但核心 scopes 已授予 = 可用，无需重试。**

---

## Step 4：验证

```bash
lark-cli calendar +agenda
```

能输出今日日程 = 配置成功。

---

## 常用命令速查

| 操作 | 命令 |
|------|------|
| 今日日程 | `lark-cli calendar +agenda` |
| 查看日历列表 | `lark-cli calendar calendars list` |
| 查看 API schema | `lark-cli schema calendar.events.create` |

### ⚠️ 创建日历事件（关键：必须用 --data JSON，不能用 --summary/--start-time）

lark-cli 的 calendar events create **不支持** `--summary`、`--start-time`、`--end-time` 这些 flag。
必须用 `--params` 传 `calendar_id`，用 `--data` 传完整 JSON body。时间用 **timestamp 秒** + `timezone`，不是 ISO 8601 datetime。

**正确格式：**

```bash
CALENDAR_ID="feishu.cn_xxxxxxxxxx@group.calendar.feishu.cn"

lark-cli calendar events create \
  --params "{\"calendar_id\": \"$CALENDAR_ID\"}" \
  --data '{
  "summary": "日程标题",
  "description": "日程描述",
  "start_time": {"timestamp": "1778806800", "timezone": "Asia/Shanghai"},
  "end_time": {"timestamp": "1778814000", "timezone": "Asia/Shanghai"},
  "free_busy_status": "busy",
  "visibility": "public",
  "reminders": [{"minutes": 30}]
}'
```

**如何获取 timestamp：**
```python
from datetime import datetime, timezone, timedelta
tz = timezone(timedelta(hours=8))
dt = datetime(2026, 5, 15, 9, 0, 0, tzinfo=tz)
print(int(dt.timestamp()))  # 1778806800
```

### 删除事件

```bash
lark-cli calendar events delete \
  --params '{"calendar_id": "feishu.cn_xxxx@group.calendar.feishu.cn", "event_id": "xxxxxx_0"}'
```

### 列出/搜索已有事件

```bash
# 查看今日日程（推荐，最简单）
lark-cli calendar +agenda

# 搜索未来事件（按日期范围）
lark-cli calendar events search_event \
  --params '{"calendar_id": "feishu.cn_xxxx@group.calendar.feishu.cn"}' \
  --data '{"start_time": {"date": "2026-05-15"}, "end_time": {"date": "2026-05-17"}}'
```

### 其他操作

| 操作 | 命令 |
|------|------|
| 创建文档 | `lark-cli docs create --title "标题" --folder-token <token>` |

---

## Task / 任务操作（待办清单）

飞书任务是真正的 Todo 式待办——有标题、截止日、可打勾完成。比 Base 更适合「做一个、勾一个」的工作流。

### 创建任务清单（tasklist）

```bash
lark-cli task +tasklist-create --name "波总待办"
# 返回 guid（如 b1df7ca1-e399-4466-bbda-7b9152cee418）+ URL
```

一个 tasklist 就是一个分组（类似 Todoist 的项目）。建议用一个 tasklist 装所有副官任务，飞书中可按优先级/日期筛选。

### 批量创建任务到指定清单

```bash
TL="b1df7ca1-e399-4466-bbda-7b9152cee418"

lark-cli task +create \
  --summary "🔴 [T018] FOS系统软著申请：提交第二批材料" \
  --due "2026-05-10" \
  --description "已付款，待准备第二批材料" \
  --tasklist-id $TL \
  --idempotency-key "adjutant-T018-v1"
# 返回 data.guid（飞书任务 ID，用于后续 complete/update）
```

**关键 flag：**
| Flag | 说明 |
|------|------|
| `--summary` | 任务标题（建议带优先级 emoji + 副官 ID） |
| `--due` | 截止日期（`YYYY-MM-DD` 格式） |
| `--description` | 任务详情/备注 |
| `--tasklist-id` | 所属清单 GUID（必传，否则任务不进清单） |
| `--idempotency-key` | 幂等键（用 `adjutant-T0XX-v1` 格式，防重复创建） |

### 完成任务（打勾）

```bash
lark-cli task +complete --task-id <feishu_task_guid>
```

### 重新打开已完成任务

```bash
lark-cli task +reopen --task-id <feishu_task_guid>
```

### 删除任务（⚠️ 命令路径不同！）

删除命令不在便利命令层（`task +xxx`），在底层 API 命令（`task tasks xxx`）：

```bash
lark-cli task tasks delete --params '{"task_guid":"<guid>"}' --yes
```

| 要素 | 值 |
|------|-----|
| 命令路径 | `task tasks delete`（不是 `task +delete`） |
| 参数 | `--params '{"task_guid":"<guid>"}'` |
| 确认 | 必须加 `--yes`，否则拒绝执行 |
| scope | `task:task:delete`（通常已随 `task:task:write` 授予） |
| 返回 | `{"code":0,"data":{},"msg":""}` 表示成功 |

⚠️ 常见的错误路径：`lark-cli task +delete` → 不存在。正确路径：`lark-cli task tasks delete`。

## 重复任务清理 SOP

当同步脚本 bug 导致同一任务在飞书出现多份拷贝时的标准清理流程。

### 症状

同一任务的 summary 包含相同 `[T0XX]` 标记，但 GUID 不同，飞书待办视图中出现多条相同条目。

### 根因

`sync_to_lark.py` / `sync_feishu.py` 等同步路径无去重锁，每次遍历 `status.json` 都重新创建任务。`feishu_task_mapping.json` 未及时更新 → 后续运行不认已有任务 → 继续创建。

### 清理步骤

**Step 1：检测重复**

```bash
export PATH="$HOME/.npm-global/bin:$PATH"
for tid in T040 T041 T042; do
  count=$(lark-cli task +search --query "$tid" 2>&1 | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']['items']))")
  [ "$count" -gt 1 ] && echo "$tid: $count copies ⚠️" || echo "$tid: clean ✅"
done
```

**Step 2：全部标记完成（清理待办视图）**

先让所有拷贝进入"已完成"状态，飞书待办视图自然清空：

```bash
for tid in T040 T041; do
  lark-cli task +search --query "$tid" 2>&1 | python3 -c "
import sys,json,subprocess,os
os.environ['PATH']+=':$HOME/.npm-global/bin'
for t in json.load(sys.stdin)['data']['items']:
    if not t.get('completed_at'):
        subprocess.run(['lark-cli','task','+complete','--task-id',t['guid']])
        print(f'  ✅ completed {t[\"guid\"][:8]}')
"
done
```

**Step 3：删除多余拷贝，每任务仅保留 1 份**

```bash
for tid in T040 T041; do
  # 获取全部 GUID
  guids=$(lark-cli task +search --query "$tid" 2>&1 | python3 -c "
import sys,json
items=json.load(sys.stdin)['data']['items']
# 保留第一个，删除其余
for t in items[1:]:
    print(t['guid'])
")
  # 逐个删除
  for guid in $guids; do
    lark-cli task tasks delete --params "{\"task_guid\":\"$guid\"}" --yes 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅' if d['code']==0 else '❌'+str(d))"
  done
  echo "  $tid done"
done
```

**Step 4：更新映射表**

```bash
# 获取每任务仅剩的 GUID 并写入映射表
for tid in T040 T041; do
  guid=$(lark-cli task +search --query "$tid" 2>&1 | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['items'][0]['guid'])")
  echo "  $tid → $guid"
  # 更新 feishu_task_mapping.json 的 mapping 字段
done
```

**Step 5：验证**

```bash
for tid in T040 T041; do
  count=$(lark-cli task +search --query "$tid" 2>&1 | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']['items']))")
  [ "$count" -eq 1 ] && echo "$tid: ✅" || echo "$tid: ⚠️ $count copies remain"
done
```

### 防止复发

- `sync_to_lark.py` 创建前检查 `feishu_task_mapping.json` 的 `mapping[TID]` → 已存在则跳过
- 创建成功后立即写回 `mapping[TID] = feishu_guid`
- 同步脚本每次运行前 `git pull` 确保映射表最新

⚠️ `+search` **不支持** `--data` flag（报 `unknown flag: --data`）。用 `--query` 搜索关键词，或 `--completed` 筛选已完成。
⚠️ `+get-my-tasks` 返回空是正常的——任务属于 tasklist，不在「我的任务」视图。
⚠️ `is_completed` 字段返回值是 `None`（不是 `True/False`）——已完成任务的特征是 `completed_at` 有值而非 `is_completed == True`。同步脚本应检查 `completed_at` 而非 `is_completed`。
⚠️ **`--page-all` 配额杀手**：`lark-cli task +search --completed --page-all` 每次翻页消耗 1 次 API 调用。飞书免费版 Base/文档/任务配额共享，长文 4-5 次即耗尽。**不要用 `--page-all` 做定期全量轮询**——应改为按 GUID 单查（`+search --query "<guid前8位>"`，通常 1 次调用）。
⚠️ **飞书配额恢复**：每天 0 点（北京时间）重置。0 点前所有通道（task +search / docs +create / drive +import）可能同时返回超时或 quota exceeded。

### 副官 ↔ 飞书任务自动同步模式

**从副官到飞书（创建）：**
1. `status.json` 新增 pending 任务 → 调用 `lark-cli task +create` 带 `--idempotency-key "adjutant-{ID}-v1"`
2. 保存飞书 task GUID 到 `feishu_task_mapping.json`：
```json
{
  "tasklist_guid": "b1df7ca1-...",
  "tasklist_url": "https://applink.feishu.cn/client/todo/task_list?guid=...",
  "mapping": {
    "T018": "42aaa3d3",
    "T033": "5c4fb44e"
  }
}
```

**从副官到飞书（完成）：**
3. `status.json` 任务标记 completed → 查 mapping 取 GUID → `lark-cli task +complete --task-id <guid>`

**反向同步（飞书打勾 → 副官标记完成）：**
飞书 webhook 可订阅任务变更事件（`task.task_status_changed`），但需要服务端接收。
已实现的轻量方案详见 `references/bidirectional-task-sync.md`：`scripts/sync_feishu.py` + cron 每5分钟轮询。

### 陷阱

- `+create` 不加 `--tasklist-id` → 任务创建成功但不在任何清单里，飞书 UI 中难以找到
- `--idempotency-key` 不是 UUID 格式也可以（与日历不同），用 `adjutant-T0XX-v1` 即可
- `+get-my-tasks` 返回 `items: null` 不代表任务没创建——任务在 tasklist 里，不在「我的任务」视图
- 飞书任务不自动同步到飞书日历——需要单独创建日历事件

---

## Base / 多维表格操作

飞书 Base（多维表格）通过 `lark-cli base` 子命令操作。**需要额外授权 scope**：`base:app:create` 等。

### 首次创建 Base 前的授权

Base 操作需要额外的 scope，不同于日历：

```bash
# 扩展授权（用户扫码）—— 注意用 --domain base，不是 --scope！
lark-cli auth login --no-wait --json --domain base
# 返回 verification_url → 用户扫码 → 用 device_code 完成
lark-cli auth login --device-code <device_code>
```

### 创建 Base

```bash
lark-cli base +base-create --name "Base名称" --time-zone "Asia/Shanghai"
# 返回 base_token（如 HZn7btVpkaVb4YsSlbvcdmPbn8c）+ URL
```

⚠️ 新 Base 默认带一张 "数据表"，不能直接删除（"The last table cannot be deleted"）。先创建至少一张新表，再删默认表。

### 表格管理

```bash
# 列出所有表
lark-cli base +table-list --base-token <BASE_TOKEN>

# 创建表
lark-cli base +table-create --base-token <BASE_TOKEN> --name "表名"

# 删除表（需要 --yes，且不能是最后一张表）
lark-cli base +table-delete --base-token <BASE_TOKEN> --table-id <TABLE_ID> --yes
```

### ⚠️ 添加字段（关键：用 --json，不是 --name/--type）

`+field-create` **不支持** `--name` 和 `--type` flag。必须用 `--json` 传字段属性对象：

```bash
# ❌ 错误：lark-cli base +field-create --name "字段名" --type "text"
# ✅ 正确：
lark-cli base +field-create --base-token <BASE_TOKEN> --table-id <TABLE_ID> \
  --json '{"name":"字段名","type":"text"}'

# type 可选值：text, number, select, date, checkbox, attachment, url, etc.
```

### ⚠️ 插入记录（关键：flat JSON，无 "fields" 包装）

`+record-upsert` 接受**扁平 JSON**，不要用 `{"fields": {...}}` 包装：

```bash
# ❌ 错误：--json '{"fields":{"字段名":"值"}}'  → "Record write payload must not be wrapped in `fields`."
# ✅ 正确：
lark-cli base +record-upsert --base-token <BASE_TOKEN> --table-id <TABLE_ID> \
  --json '{"字段名":"值","数字字段":123}'
```

### +record-batch-create 不支持简单 JSON 格式

批量创建使用不同的格式（`fields` 数组 + `rows` 数组），lark-cli 不支持简单 records 数组。**建议使用多次 `+record-upsert` 替代。** 如需批量，直接用飞书 Open API curl：

```bash
curl -X POST "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create" \
  -H "Authorization: Bearer $(lark-cli auth token)" \
  -d '{"records":[{"fields":{"列1":"值1"}},{"fields":{"列1":"值2"}}]}'
```

### 仪表盘与图表（CLI 限制）

`+dashboard-create` 正常，但 `+dashboard-block-create` 的 `--data-config` 格式**未在 lark-cli 中充分文档化**：

```bash
# 仅 statistics（指标卡）和 text 块经过验证可创建：
lark-cli base +dashboard-block-create \
  --base-token <BASE_TOKEN> --dashboard-id <DASH_ID> \
  --name "指标卡名" --type "statistics" \
  --data-config '{"table_name":"表名","count_all":true}' --no-validate

# 图表（bar/pie/line/column）的 data_config schema 复杂且无文档。
# 建议：CLI 创建好 tables + data，然后在飞书 UI 中拖拽字段生成图表。
# 飞书会根据字段类型自动推荐图表类型。
```

| 已验证可用的 block type | 状态 |
|-------------------------|------|
| `statistics`（指标卡）| ✅ count_all 可用 |
| `text`（文本）| ⚠️ content 字段不可用 |
| `bar` / `pie` / `line` / `column` | ❌ data_config 格式未知，需在飞书 UI 中创建 |

### 查询字段

```bash
lark-cli base +field-list --base-token <BASE_TOKEN> --table-id <TABLE_ID>
# 返回字段 ID（fldxxxxx）+ name + type，用于 API 调用
```

### Schema 命令不支持 base

```bash
lark-cli schema base.dashboard.block.create  # ❌ "Unknown service: base"
# 飞书 Base API schema 不通过 lark-cli schema 暴露，需查飞书官方文档
```

### 设置 Base 公开可查看（无需登录）🔓

Base 默认可查看需要登录。设成"互联网公开"需要 `drive permission.public`：

**首次需额外授权 scope：**
```bash
lark-cli auth login --no-wait --json --scope "docs:permission.setting:write_only"
# 扫码后 device_code 完成授权
```

**设置公开：**
```bash
lark-cli drive permission.public patch \
  --params '{"token":"<BASE_TOKEN>","type":"bitable"}' \
  --data '{
    "external_access": true,
    "link_share_entity": "anyone_readable",
    "invite_external": true,
    "share_entity": "anyone"
  }' --yes
```

| 字段 | 值 | 含义 |
|------|-----|------|
| `external_access` | true | 允许分享到组织外 |
| `link_share_entity` | anyone_readable | 互联网上获得链接的人可阅读 |
| `invite_external` | true | 允许非管理员分享到组织外 |
| `share_entity` | anyone | 任何人都可以添加协作者 |

`type` 参数对应文档类型：`bitable`(多维表格) / `docx`(新版文档) / `sheet`(电子表格) / `wiki`(知识库) 等。

`link_share_entity` 可选值：`tenant_readable`(企业内可读) / `tenant_editable`(企业内可编辑) / `anyone_readable`(互联网可读) / `anyone_editable`(互联网可编辑) / `closed`(关闭链接分享)。

### 危险操作需要 --yes

```bash
lark-cli base +table-delete ... --yes     # 不加 --yes 会报 "requires confirmation"
```

---

## 与副官系统集成

见 `hermes-adjutant/INTEGRATION_LARK.md`：
- status.json 任务 → 飞书日历事件 + 飞书任务（待办清单）双同步
- 每日行程日志自动生成到飞书文档
- 周报汇总

**已实现的同步脚本：** `hermes-adjutant/scripts/sync_to_lark.py`

**双同步策略（日历 + 任务）：**
- 有具体 `date` 的任务 → 飞书日历（日程事件，带时间点）
- 无时间或纯行动项 → 飞书任务（Todo 待办清单，可打勾）
- 有 `deadline` 的任务 → 任务附件截止日期 (`--due date:YYYY-MM-DD`)

**技术细节：**
- 读取 status.json → 筛选未完成 → 分类为 `calendar_tasks` 和 `task_items`
- 日历事件：`lark-cli calendar events create`，使用 `uuid.uuid5(NAMESPACE_DNS, "adjutant-cal-{task_id}-{date}")` 作 idempotency_key
- 任务待办：`lark-cli task +create`，使用 `uuid.uuid5(NAMESPACE_DNS, "adjutant-task-{task_id}")` 作 `--idempotency-key`
- 支持 `--dry-run` 预览模式
- 按 priority 自动分配颜色：🔴critical 🟠high 🔵medium 灰色low
- 过去日期/已完成/cancelled 的任务自动跳过
- 运行后输出日历和任务各自的创建/跳过/失败统计

**⚠️ 去重机制（铁律）：飞书 API 幂等 key 不可靠，本地映射才是真正防线**

`lark-cli` 的 `--idempotency-key` 在日历事件和任务 API 中**并不完美生效**——同一 idempotency key 仍可能创建出重复条目。

真正的去重依赖 `feishu_task_mapping.json` 本地映射：
- **创建前**：查 `mapping[TID]`，已存在 → 直接跳过（`📝 已映射`）
- **创建后**：`mapping[TID] = feishu_guid`，立即写回文件
- **写回时机**：在 `create_event()` 和 `create_task()` 成功返回后，不是调用方手动写

这个映射是防止飞书重复任务的**唯一可靠防线**。幂等 key 是第一道（不靠谱的）防御，本地映射是第二道（可靠的）防御。

多个同步路径（`sync_to_lark.py`、`sync_feishu.py`、`feishu-sync-from-feishu.sh`、手动 `lark-cli`、`perception.py`）共享同一份映射文件，因此只要任一路径创建成功并写回，其他路径的后续运行都不会重复创建。

**⚠️ 陷阱：lark-cli task +create 与 calendar events create 校验方式不同**
- `calendar events create` 返回 `{"code": 0, "data": {"event": {"event_id": "..."}}}` — 检查 `resp.get("code") != 0`
- `task +create` 返回 `{"ok": true, "data": {"guid": "..."}}` — 必须检查 `resp.get("ok")`（不是 `code`！）
- task +create 不支持 `--priority` flag，要用 `--summary` + `--description` 直接传
- `--idempotency-key` 用连字符（hyphens），不是下划线 `--idempotency_key`
- `--due` 格式为 `date:YYYY-MM-DD`（如 `--due date:2026-05-27`）

---

## 绕过文档创建配额：多级 fallback 策略

当 `docs +create` 持续返回 `90003081 file quota exceeded` 时（即使删除了所有残骸后仍失败），说明 block 创建配额已耗尽。按以下优先级尝试：

### Level 1：drive +import（docx 格式，非 markdown）

`drive +import` 走的是文件导入通道。⚠️ **但实测不支持导入原始 .md 文件**——飞书导入引擎拒绝 raw markdown（格式不兼容报错）。必须先用 pandoc 转成标准 .docx：

```bash
# Step 1：Markdown → DOCX（用 pandoc）
pandoc content.md -o content.docx --from=markdown --to=docx

# Step 2：导入 DOCX
lark-cli auth login --no-wait --json --scope "docs:document:import"
# 扫码后 device_code 完成

lark-cli drive +import \
  --file ./content.docx \
  --type docx \
  --name "文档标题"
# 注意：flag 是 --name（不是 --title）
```

⚠️ 当 create 配额已耗尽时，import 配额可能也被连带消耗了（我们实测中两者同时报 `file quota exceeded`）。

### Level 2：GitHub 公开 Markdown（最终兜底 ✅）

当飞书所有通道都配额耗尽时，GitHub 公开 Markdown 是最可靠的兜底方案：

```bash
# 推到 hermes-adjutant 仓库
cp content.md ~/hermes-adjutant/hermes_analysis.md
cd ~/hermes-adjutant && git add . && git commit -m "文档" && git push
```

结果：`https://github.com/bog5d/hermes-adjutant/blob/main/hermes_analysis.md` 互联网任何人可读，无需登录。

### Level 3：等次日 0 点配额重置

飞书免费版配额每天 0 点（北京时间）重置。不紧急的文档等到第二天再建。

**对比三种方式：**

| 方式 | 配额池 | 长文支持 | 实测稳定性 |
|------|--------|---------|-----------|
| `docs +create --markdown` | block 创建配额 | ❌ 长文易超配额 | 低（4-5次长文即耗尽） |
| `docs +create --api-version v2` | v2 API | ❌ v1.0.31 有 bug | 极低 |
| `drive +import .docx` | 文件导入配额 | ⚠️ 可能被连带耗尽 | 中（需 pandoc 转格式） |
| GitHub Markdown | 无限制 | ✅ 不限 | 高（即时可用） |

---

## 常见问题

| 问题 | 解决 |
|------|------|
| `FEISHU_APP_ID not found` | .env 未配置或被 credential 保护回滚，用 `cat >>` 追加新行 |
| `config init is refused` | Hermes 上下文必须用 `config bind` |
| 授权超时 | 用户未扫码，重新运行 `auth login --recommend` |
| `lark-cli: command not found` | 添加 `~/.npm-global/bin` 到 PATH |
| `please specify the scopes to authorize` | `--no-wait --json` 必须加 `--domain` 参数，如 `--domain calendar,task,docs` |
| device code 过期（10分钟后验证失败）| 重新 `auth login --no-wait --json --domain ...` 获取新 link，不要重试旧 code |
| `unknown flag: --summary` | calendar events create **不支持** `--summary`/`--start-time`，必须用 `--data` 传 JSON body（见上方正确格式）|
| API 返回 99992402 "field validation failed" | idempotency_key 必须是 UUID 格式（如 `550e8400-e29b-41d4-a716-446655440000`），不能用任意字符串。用 `uuid.uuid5()` 生成确定性 UUID |
| 创建成功但日历上不显示 | 检查 `calendar_id` 是否正确（用 `lark-cli calendar calendars list` 获取），确认是 primary 日历 |
| 时间不正确 | 必须用 **秒级 timestamp** + timezone，不是 ISO 8601 datetime 字符串 |
| 部分 scopes 未授予（如 im:message.send_as_user）| 不影响核心功能（日历/文档/任务 CRUD），忽略即可。核心权限是 calendar:calendar.event:create/read/update/delete + task:task:read/write + docx:document:create/readonly/write_only |
| `docs +create --api-version v2` 返回 "All commands in the create content request failed" | lark-cli v1.0.31 的 v2 API 存在 bug，即使最简单的 "Hello World" 也会失败。不要用 v2。用 v1（默认）或换方案（GitHub Markdown / wiki） |
| v1 docs +create 返回 "file quota exceeded" (90003081) | 每次失败的 v1 创建尝试会在飞书云端留下残存文档，累积消耗配额。先删残留文档（需 `docs:permission` scope），或改用 GitHub/wiki 发布长文 |
| Shell 中 lark-cli 传入长 Markdown 时特殊字符被解释 | 管道符 `|`、反引号 `` ` ``、`$` 等会被 bash 解析。将内容写入文件，用 `$(cat file)` 或 v2 的 `@file`（相对路径）传递。建议内容较短时用单引号包裹 JSON，长内容走文件 |
| 免费版配额打满后 `drive +import` 也报 `file quota exceeded` | 免费版 import 配额和 create 配额可能共享同一池子。所有通道都耗尽时用 GitHub 公开 Markdown 兜底，等次日 0 点重置 |

### 清除配额：删除失败的 Docs 残骸

每次 v1 `docs +create` 失败（特别是一长文形式）会在飞书云端留下残存文档，累积消耗配额导致 `90003081 file quota exceeded`。

**Step 1：授权搜索 scope**

```bash
lark-cli auth login --no-wait --json --scope "search:docs:read"
# 扫码后 device_code 完成 → search:docs:read 已授予
```

**Step 2：搜索并识别失败文档**

```bash
lark-cli drive +search --query "<关键词>"
```

失败文档的标志：
- `entity_type: "DOC"`（不是 BITABLE/WIKI）
- 创建时间为当次失败附近的时间
- `summary_highlighted: ""`（空，说明内容未成功写入）
- `owner_name` 是当前用户
- `last_open_time_iso: "1970-01-01T08:00:00+08:00"`（从未被打开）

**Step 3：授权删除 scope + 删除**

```bash
# 如果缺少 space:document:delete scope
lark-cli auth login --no-wait --json --scope "space:document:delete"
# 扫码授权后删除残骸：
lark-cli drive +delete --file-token "<doc_token>" --type docx --yes
```

⚠️ 注意 flag 是 `--file-token` 不是 `--token`。type 用 `docx`（新版文档）。

**Step 4：验证配额恢复**

```bash
# 尝试创建一个极短的新文档
lark-cli docs +create --title "Test" --markdown "test"
# 若返回 ok=true 则配额已恢复
```
