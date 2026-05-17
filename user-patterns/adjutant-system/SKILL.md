---
name: adjutant-system
title: "Hermes 副官系统 — 持久任务记忆 + 云端同步 + 夜间预研"
description: "为波总搭建的异步参谋长系统。支持任务记忆（独立SQLite）、GitHub自动同步（任何AI可接盘）、Night Shift夜间预研、Human-in-the-Loop早间校验。"
trigger: "波总说要做副官系统、记录日程、作异步参谋长、或要求任务记忆永不丢失"
---

## 核心架构

```
波总口语说任务/行程
    ↓
Hermes 解析 → 写入 adjutant.db（独立 SQLite）
    ↓ 触发同步
sync.py → 更新 GitHub 仓库 hermes-adjutant
    ├── diary/YYYY-MM-DD.md      ← 每日原始记录
    ├── tasks/active.json         ← 活跃任务（状态机）
    ├── tasks/completed.json      ← 已完成归档
    ├── prep/YYYY-MM-DD.md       ← Night Shift 预研弹药
    ├── status.json              ← 当前完整快照（机器可读）
    └── logs/changelog-YYYYMM.md  ← 变更日志（其他AI可回溯）
```

**关键设计原则：**
- 独立于对话记忆（不受session过期影响）
- 云端同步（电脑没电≠数据丢失）
- 格式标准化（换一个AI也能直接读取接盘）
- 零学习成本（波总口语说，我自动转结构化）

## 仓库信息

- **GitHub**: https://github.com/bog5d/hermes-adjutant （私有）
- **第一入口**: `AGENTS.md`（AI 操作手册）→ `status.json`（当前快照）
- **6个脚本全部就绪** — 覆盖 Phase 1-5

## 目录结构

```
~/.hermes/adjutant/
├── db/adjutant.db                    ← 本地SQLite记忆仓（不进git）
└── repo/hermes-adjutant/             ← GitHub云端同步仓库
    ├── README.md                     ← 人类读（路线图 + 快速开始）
    ├── AGENTS.md                     ← AI 操作手册（7条规则 + Phase 3/4/5 新指令）
    ├── ARCHITECTURE.md               ← 技术规范（全格式 Schema）
    ├── scripts/
    │   ├── init_db.py                ← Phase 1: 建表 + 自动迁移 + seed
    │   ├── sync.py                   ← Phase 1: db→全文件+FTS索引→git push（幂等）
    │   ├── night_shift.py            ← Phase 2: 凌晨预研模板（--date --llm --dry-run）
    │   ├── handoff.py                ← Phase 3: 多AI交接协议（--from --to --push --list）
    │   ├── query.py                  ← Phase 4: 自然语言查询（FTS5 + LIKE降级）
| `scripts/advisor.py`                | Phase 5: 风险预警（`--json --push --cron`）|
| `scripts/executor.py`              | Phase 6: 执行引擎（任务事件→动作匹配→执行）|
    ├── status.json                   ← 当前全景快照（自动生成，含claimed_by字段）
    ├── diary/YYYY-MM-DD.md           ← 每日记录（任务+口语整合）
    ├── tasks/active.json             ← 活跃任务详情（含认领信息）
    ├── tasks/completed.json          ← 已完成归档
    ├── prep/YYYY-MM-DD.md            ← Night Shift产出（背景+决策对比+弹药清单）
    ├── logs/
    │   ├── changelog-YYYYMM.md       ← 变更日志（按月归档）
    │   └── handoff-*.md              ← Phase 3: 交接文件
    └── alerts/YYYY-MM-DD.md          ← Phase 5: 预警报告
```

## 数据库Schema（adjutant.db）— Phase 3/4 扩展版

```sql
CREATE TABLE diary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,          -- YYYY-MM-DD
    raw_text TEXT NOT NULL,      -- 波总原始口语记录
    category TEXT DEFAULT '',    -- 分类标签
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id TEXT PRIMARY KEY,         -- T001, T002, ...
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    priority TEXT DEFAULT 'medium',  -- critical/high/medium/low
    status TEXT DEFAULT 'pending',   -- pending/in_progress/completed/cancelled
    deadline TEXT DEFAULT '',        -- YYYY-MM-DD HH:MM
    task_date TEXT DEFAULT '',       -- 任务所属日期 YYYY-MM-DD
    task_time TEXT DEFAULT '',       -- 具体时间 HH:MM
    category TEXT DEFAULT '',        -- 融资/接待/企业治理/个人/行程
    key_contacts TEXT DEFAULT '[]',  -- 关键人（JSON array）
    claimed_by TEXT DEFAULT '',      -- Phase 3: 认领者标识 (hermes/claude/copilot)
    claimed_at TIMESTAMP,            -- Phase 3: 认领时间
    cancel_reason TEXT DEFAULT '',
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE changelog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT DEFAULT '',
    action TEXT NOT NULL,          -- created/updated/completed/cancelled/claimed/released/conflict
    detail TEXT DEFAULT '',
    operator TEXT DEFAULT '',      -- Phase 3: 操作者标识
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE handoff_logs (        -- Phase 3: 交接记录
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    summary TEXT NOT NULL,
    active_tasks TEXT DEFAULT '[]', -- JSON: 进行中的任务ID列表
    pending_issues TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Phase 4: FTS5 全文搜索（独立表，非 content= 模式）
CREATE VIRTUAL TABLE diary_fts USING fts5(
    diary_id UNINDEXED, date, raw_text, category
);
CREATE VIRTUAL TABLE tasks_fts USING fts5(
    task_id UNINDEXED, title, description, category, key_contacts
);
```

## 工作流（完整版 — Phase 1-5）

### Phase 1 — 本地记忆 + GitHub 双向同步

波总口语说 → Hermes 解析 → 写入 adjutant.db → 触发 sync.py

```
sync.py 流程：
  1. 读取 adjutant.db 最新数据
  2. 生成 status.json（按优先级+日期排序，含 claimed_by）
  3. 生成 diary/YYYY-MM-DD.md（整合tasks表+diary表）
  4. 生成 tasks/active.json + tasks/completed.json
  5. 追加 logs/changelog-YYYYMM.md（24小时内变更）
  6. 重建 FTS5 全文索引（Phase 4）
  7. git add -A → git commit → git push
  8. 幂等：无变化自动跳过，文件内容不变不写盘

调用方式：
  python3 repo/hermes-adjutant/scripts/sync.py
  python3 repo/hermes-adjutant/scripts/sync.py --dry-run   # 预览
  python3 repo/hermes-adjutant/scripts/sync.py -m "msg"     # 自定义commit
```

### Phase 2 — Night Shift 夜间预研

```bash
python3 scripts/night_shift.py                     # 为明天生成
python3 scripts/night_shift.py --date 2026-05-12   # 指定日期
python3 scripts/night_shift.py --dry-run            # 预览
```

产出 prep/YYYY-MM-DD.md：背景分析框架 + 决策对比模板 + 弹药清单 + 早间确认

### Phase 3 — 多 AI 协作协议

```bash
python3 scripts/handoff.py --from hermes --to claude       # 生成交接文件
python3 scripts/handoff.py --from hermes --to claude --push # 生成+push
python3 scripts/handoff.py --list                           # 历史交接
```

- 任务认领：`claimed_by` + `claimed_at` 字段
- 冲突检测：同一任务被两个AI认领时记录 `action='conflict'`
- 交接文件：`logs/handoff-YYYYMMDD-HHMM-{from}-to-{to}.md` 自动生成
- 不抢夺他人已认领的 in_progress 任务

### Phase 4 — 自然语言查询

```bash
python3 scripts/query.py "穆博士"                    # FTS5优先→LIKE降级
python3 scripts/query.py "融资 OR 接待"              # OR搜索
python3 scripts/query.py --contacts "老唐"            # 关联人
python3 scripts/query.py --recent                     # 最近7天
```

### Phase 5 — 智能预警

```bash
python3 scripts/advisor.py                  # 四种检测
python3 scripts/advisor.py --json            # JSON输出
python3 scripts/advisor.py --push            # 写入alerts/ + push
```

检测项：⏰ deadline风险（48h） / ⚡ 时间冲突 / 📊 认领过载（>5） / 🧟 僵尸任务（>7d无认领）

---

## DB迁移模式（重要）

init_db.py 采用三步初始化法，避免旧表缺列导致 CREATE INDEX 报错：

```
1. BASE_SCHEMA  — 建基础表（不含新列索引）
2. run_migrations() — ALTER TABLE 补 missing columns（通过 PRAGMA table_info 检测）
3. INDEX_SCHEMA — 建索引（含新列的索引）
```

在 sync.py 启动时也运行 init_db() 确保迁移始终执行。

## 波总沟通习惯（针对副官场景）

| 波总口语 | 我做的事 |
|---------|---------|
| "安排一下XX" | 创建任务，写入 diary + tasks，同步 |
| "XX搞完了/搞定了" | 标记任务 completed，更新 changelog |
| "XX改到后天" | 更新 deadline，写 changelog |
| "XX取消了" | 标记 cancelled，记录原因 |
| "帮我看看还有什么没做" | 读 status.json，列当前 active 任务 |
| "另一个AI接一下" | 另一个AI直接拉 GitHub repo 读 status.json |

## JSON格式（status.json，机器可读）

```json
{
  "date": "2026-05-09",
  "updated_at": "2026-05-09T14:30:00+08:00",
  "summary": {
    "total": 12,
    "pending": 8,
    "completed": 2,
    "cancelled": 2
  },
  "tasks": [
    {
      "id": "uuid",
      "title": "跟穆博士沟通融资对齐",
      "status": "pending",
      "priority": "high",
      "deadline": "2026-05-09 14:00",
      "category": "融资",
      "key_contacts": ["穆博士"]
    }
  ]
}
```

## 初始认证（首次使用）

需要波总提供：
1. GitHub Personal Access Token（repo 写入权限）：`ghp_xxx`
2. 推送方式（可选）：
   - **PushDeer**：装 App，给 pushkey
   - **企业微信/钉钉/飞书**：建群机器人，给 Webhook URL
   - **Bark**（iOS）：装 App，给推送 URL

### Phase 6 — 执行引擎

```bash
python3 scripts/executor.py --task T020         # 对单个任务匹配并执行
python3 scripts/executor.py --all-pending        # 所有待处理任务
python3 scripts/executor.py --dry-run            # 预览不执行
python3 scripts/executor.py --list-rules         # 列出规则
python3 scripts/executor.py --list-confirm       # 列出待确认项
python3 scripts/executor.py --confirm <N>        # 确认并执行
```

架构：Task事件 → Action Matcher → Execution Gate → Action Runner

**4个执行器**：
| 执行器 | 功能 |
|---|---|
| `telegram_notify` | 发 Telegram 消息到波总 |
| `fos_dashboard` | 更新 ~/cangjie-fos/data/adjutant_status.json |
| `obsidian_note` | 写仓颉笔记（Obsidian vault/副官任务/） |
| `webhook` | POST 到外部 URL |

**Execution Gate**：`auto`（自动执行）vs `confirm`（写入待确认队列，需波总确认）

**规则配置**：`~/.hermes/adjutant/config/executor_rules.yaml`（不存在时用内置默认规则）

**环境变量**（`~/.hermes/adjutant/.env`）：
- `TELEGRAM_BOT_TOKEN` — Telegram Bot token
- `TELEGRAM_CHAT_ID` — 波总 DM chat_id

**集成点**：每次 adjutant-brain-dump 写完任务后，sync → executor

| 时间 | 名称 | 脚本 | 功能 |
|------|------|------|------|
| 02:00 | Night Shift | `scripts/night_shift.py --push` | 读取明日高优任务，生成 prep/ + LLM自动填充 |
| 08:00 | Morning Brief | `scripts/morning_brief.py --push` | 今日排程 + 昨日遗留确认 + Human-in-the-Loop |
| 23:00 | 晚间心灵日记 | （独立 cron） | Hermes 每日视角总结 |

### LLM 自动填充（Night Shift 增强）

API Key 存放：`~/.hermes/adjutant/.env`（chmod 600, gitignored）
格式：`DEEPSEEK_API_KEY=sk-xxx`

night_shift.py 行为：
- 启动时调用 `_load_env()` 读取 `.env` 中的环境变量
- 若 `DEEPSEEK_API_KEY` 存在且任务非空，自动启用 LLM 填充
- `--no-llm` 标志可禁用
- LLM 调用：`urllib.request` → DeepSeek API (`deepseek-chat`)，temperature=0.7, max_tokens=2000
- 输出追加到 prep 文件末尾 `## 🤖 AI 预研（自动生成）`
- 失败不阻断主流程，仅打印警告

---

## ⚠️ 数据源架构铁律（2026-05-17 确立）

**GitHub status.json = 单一事实源。SQLite adjutant.db = 可淘汰的遗留缓存。**

### 血的教训

Q3 审计引擎连续多天报 T021/T011-T013 假阳性，根因是 **两个数据源各说各话**：

| 数据源 | 我们更新它？ | Q3 审计读它？ | 结果 |
|--------|------------|-------------|------|
| status.json | ✅ 每次口头更新 | ❌ advisor.py 不读 | 白改 |
| adjutant.db | ❌ 只改过 status.json | ✅ advisor.py 读 | 永远过时 |

**为什么 SQLite 不能做主源：**
- SQLite 是本地文件，不在 Git 里，其他 AI 克隆不到
- 每次 status.json 变更后需手动 sync，漏一次就裂
- 双重写入（改 status.json + 改 SQLite）必然不同步

**正确处理方式：**
1. **所有脚本直接读 `status.json`**（`open+json.load`），零 SQLite 依赖
2. 如果真需要 SQLite（查询性能），它是**只读缓存**，由 status.json 单向同步
3. 任何任务状态变更 → 改 status.json → git push — 一条线

### 已修复（2026-05-17）
- `advisor.py`：完全重写，移除 SQLite 依赖，直接读 status.json
- `perception.py`：移除 SQLite import + DB_PATH + sync_status_to_sqlite
- 待修复：morning_brief.py, night_shift.py, query.py, executor.py, handoff.py, sync.py

---

## 关键教训

### 架构教训
1. **GitHub status.json 是根** — 一切数据由此派生，不做反向同步
2. **杜绝双写** — 一次变更只写一个地方。多数据源 = 多点故障
3. **内存不能存实际数据** — adjutant.db 是缓存不是真相源
4. **同步要立即触发** — 每次写入后自动 push，不等到 cron 定时
5. **人形回路不可少** — 早8点推送必须先问确认，再执行
6. **格式要严格但人类输入要宽松** — 波总口语即可，不要让他学格式
6. **路线图 [x] 必须代码跟上** — 标记完成前必须验证代码存在且跑通。先写脚本再标状态。
7. **脚本放在 repo/scripts/ 不在 adjutant/scripts/** — 脚本属于仓库（可被其他AI克隆），数据库属于本地（不进git）
8. **Cron 是最后一步不是第一步** — 先让脚本能跑通（手动验证），再挂 cron。这样 cron 失败时你知道是脚本问题还是调度问题

### 技术坑（2026-05-10 实踩）

9. **SQLite Row 没有 `.get()` 方法** — 必须用 `r["key"]` 配合 `if "key" in r.keys()` 检查，否则 AttributeError
10. **FTS5 中文分词问题** — unicode61 tokenizer 不处理中文分词，"穆博士"这种单嵌词 FTS 搜不到。方案：FTS5 优先 + LIKE '%关键词%' 降级兜底
11. **FTS5 INSERT 必须显式 commit()** — `conn.executemany()` 对 FTS5 虚拟表的写入不会自动提交，必须 `conn.commit()` 否则数据丢失
12. **DB 损坏恢复** — FTS5 操作可能导致 "database disk image is malformed"，直接 `rm adjutant.db` 然后 `init_db.py --seed` 重建
13. **DB 列级迁移三步法** — BASE_SCHEMA(建基础表) → run_migrations(ALTER TABLE补列) → INDEX_SCHEMA(建含新列索引)。如果 CREATE INDEX 写在 CREATE TABLE 中，旧表缺列时直接报错退出
14. **sync.py 幂等性** — 每次文件写入前对比内容，不变不写（避免不必要的 git commit 和 timestamp 抖动）

### 波总交互教训
15. **一次性交付** — 波总不喜欢每阶段确认。Phases 3-6 一起写，写完自测，测完 push。输出总结而非过程。
16. **诚实标状态** — 路线图的 [x] 不能提前标。Phase 1/2 在文档里标了完成，实际 scripts/ 全空，被波总一眼看出来。改正：代码跑通后再标状态。

### Shell/脚本坑
17. **不要用 `python3 -c` 写含中文多行字符串** — shell 会把中文标点（如 `。`、`：`）解释为命令分隔符导致 SyntaxError。改法：写到 `/tmp/adj_update.py` 文件再 `python3 /tmp/adj_update.py`。
18. **任务描述里的分析方案要沉淀** — 波总说"你的思路也可以沉淀下来"。复杂分析（如 FOS 部署方案 A/B/C）不应只口头说，写入任务的 `description` 字段，让后续 AI 接手时直接读取。
19. **API Key 绝不能进 Git** — 存 `.env` 文件 + chmod 600 + `.gitignore`。直接写入环境变量或 `.env` 文件，绝不出现在 commit message 或代码注释中。
