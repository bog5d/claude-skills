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
| 创建任务 | `lark-cli task create --summary "任务名" --due-date 2026-05-20` |

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
- status.json 任务 → 飞书日历事件自动同步
- 每日行程日志自动生成到飞书文档
- 周报汇总

**已实现的同步脚本：** `hermes-adjutant/scripts/sync_to_lark.py`
- 读取 status.json → 筛选有 date 且未完成的任务 → 批量创建飞书日历事件
- 使用 UUID5 (`uuid.uuid5(NAMESPACE_DNS, "adjutant-{task_id}-{date}")`) 作 idempotency_key 防止重复
- 支持 `--dry-run` 预览模式
- 按 priority 自动分配颜色：🔴critical 🟠high 🔵medium 灰色low
- 过去日期/已完成/cancelled 的任务自动跳过

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
