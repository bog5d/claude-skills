---
name: finance-hub
description: 波总个人财务中枢 v2.0 — 债务追踪 + 消费分析 + 还款日预测 + 暴力催收。当你收到"还了XX YY元""花呗清了""我的债务""截图""消费"等财务相关指令时使用。
category: productivity
trigger: 还了|还款|债务|负债|花呗|借呗|还款进度|财务|欠款|清债|消费|截图|账单|支付宝|微信账单|报销|基金
---

# 财务中枢 (Finance Hub)

波总的个人债务/还款追踪系统，独立于副官任务管理之外的第二个职能模块。

## 文件位置（铁律：只有一个路径）

```
🛑 绝对不要编辑 ~/.hermes/adjutant/finance/        ← 这只是一个副本
✅ 所有操作都去 ~/.hermes/adjutant/repo/hermes-adjutant/finance/  ← Git 仓库（唯一事实源）
```

**铁律：直接编辑 REPO 路径，不要碰工作副本。** `patch()`, `write_file()` 等所有操作的目标路径必须是 `~/.hermes/adjutant/repo/hermes-adjutant/finance/`。工作目录 `~/.hermes/adjutant/finance/` 仅供 python 脚本输出，不是给人手改的。

修改后：`cd ~/.hermes/adjutant/repo/hermes-adjutant && git add -A && git commit -m "finance: ..." && git push`

如果确实从工作副本改了（如跑脚本），必须立即：
```bash
cp ~/.hermes/adjutant/finance/debts.json ~/.hermes/adjutant/repo/hermes-adjutant/finance/
cp ~/.hermes/adjutant/finance/transactions.json ~/.hermes/adjutant/repo/hermes-adjutant/finance/
cd ~/.hermes/adjutant/repo/hermes-adjutant && git add -A && git commit -m "sync: ..." && git push
```
commit 前用 `diff` 检查两副本一致。

| 文件 | 用途 |
|------|------|
| `debts.json` | 全部债务：`active`（待还）+ `cleared`（已清）+ `meta` |
| `config.json` | 12 个里程碑 + 8 个成就定义 |
| `transactions.json` | 还款流水（每条一笔记录） |
| `snapshots/YYYY-MM-DD.json` | 每周自动快照 |
| `scripts/finance.py` | 核心引擎（repay / report / daily / snapshot / milestones / set-duedate / due-check） |
| `scripts/expenses.py` | 🆕 消费追踪引擎（add / batch / report / summary / recat / screenshot） |
| `scripts/nag_screenshots.py` | 🆕 暴力催收脚本（检查昨日截图到位否，没到位输出催收消息） |
| `scripts/import_csv.py` | 🆕 CSV 流水导入器（自动识别支付宝/微信，解析+去重+分类入库） |
| `scripts/daily_report.sh` | 🆕 日报生成包装脚本（cron 用） |
| `scripts/gamification.py` | 🆕 游戏引擎：成就/里程碑检测 + 归途志叙事。`check`检测新解锁，`narrative`生成叙事 |
| `scripts/generate_starfire.py` | 🆕 HTML可视化生成器：从3个JSON → 归途星火页面 → 截图发给波总 |
| `expenses.json` | 🆕 消费数据 + 17 类别规则引擎 + 截图记录 |

## ⚠️ 波总沟通偏好（本会话确认）

| 场景 | 怎么做 | 原因 |
|------|--------|------|
| 波总问"我的负债/总负债" | **先问"哪些有变动？"** 收集更新后再出全景 | 数据可能过时，直接输出易错 |
| 波总说"XX抵掉了/用其他方式"（非现金） | amount=0 + notes="其他方式抵账"，移入 cleared | 非现金还款，不应入还款流水 |
| 花呗截图 | "7月账单累计 ¥X" = **总待还余额**，直接更新 | 波总确认单数即总账，不要追问"新增还是总欠" |
| 拿去花截图 | "全部待还 ¥X" = 总余额；"X月X日待还 ¥Y" = 未出账部分 | 拿去花有"未出账"概念，总待还 > 未出账金额 |
| 新增自债（非现金动用） | 创建 ID=I001/2/3, type="其他", rate=0, 按 I 系列连续编号 | 如基金储备款被消费占用，1-2个月内填回 |
| 短期承诺（1-2月填回） | 在 notes 标注 "X个月内填回" 时间预期 | 让波总明确还款时间窗口 |
| 还款日 | 截图中"还款日X月X日"就是到期日，写入 `due_date` | 平台债总有固定还款日 |

## 交互模式：三种消息，不会搞混

| 波总说什么 | 你做什么 | 数据去向 |
|-----------|----------|----------|
| 「T051完成了」「新增任务XX」 | 副官任务管理 | `status.json` → Git push |
| **「还了花呗 2000」「妈妈还了 5000」** | **财务中枢还款** | `debts.json` → Git push |
| 「花呗清了」「XX还完了」 | 全额清空该债，移入 `cleared` | Git push |
| 「我的债务」「财务报告」 | 运行 `finance.py report` 输出大盘 | — |
| 「XX新增 ZZ 元」「借了 XX ZZ」 | 手动追加到 `debts.json` active 列表 | Git push |
| **「发截图」（微信/支付宝账单）** | **OCR → 去重 → 分类 → 写入 expenses.json** | `expenses.json` → Git push |
| **「发截图」（花呗/拿去花/度小满）** | **OCR → 更新 debts.json 金额 + 提取还款日** | `debts.json` → Git push |
| 「消费分析」「这个月花了多少」 | 运行 `expenses.py report -t monthly` | — |
| 「设置花呗还款日」 | `finance.py set-duedate -c "花呗" -d YYYY-MM-DD` | `debts.json` → Git push |

## 还款记录流程（铁律）

```
波总说："还了花呗 2000"
  ↓
1. cd ~/.hermes/adjutant/repo/hermes-adjutant
2. git pull origin main   ← 先拉最新（其他 AI 可能已更新）
3. python3 finance/scripts/finance.py repay -c "花呗" -a 2000
4. 读 JSON 输出，确认金额和剩余
5. 反馈给波总：已记录 + 当前余额 + 进度条 + 里程碑变化
6. git add -A && git commit -m "finance: 还花呗2000" && git push
```

每笔还款后必须立即 git push。数据永不失忆。

## 关键数据字段

每笔债务 (`debts.json` → `active[].*`)：

```json
{
  "id": "F001",
  "creditor": "妈妈",
  "type": "亲友 | 平台",
  "amount": 135100,
  "rate": 0.047,
  "notes": "备注",
  "updated_at": "2026-05-31 20:41",
  "source": "花呗App截图 2026-05-31"
}
```

- `updated_at` — 每笔债的数据更新时间，报告里必须展示
- `source` — 数据来源（App截图/波总手输/还款记录）
- `rate` — 年利率，`null` = 无息

## 当前债务总览（基准：2026-05-31）

| 类别 | 金额 |
|------|------|
| 亲友债 | ¥456,650（16笔） |
| 平台债 | ¥69,727（4笔：花呗/拿去花/度小满/工行） |
| 总负债 | ¥526,377 |
| 已清 | 10笔 / ¥210,000+ |

## 里程碑路线

```
🗺️ ¥521,262 起点
⚔️ ¥500,000 → 🛡️ ¥450,000 → 🏹 ¥400,000
🔥 ¥350,000 → 💨 ¥300,000 → 🌅 ¥250,000
👁️ ¥200,000 → 🏰 ¥150,000 → ⚡ ¥100,000
🎯 ¥50,000  → 👑 ¥0 Zero Day
```

## 🆕 v2.0 自动推送（4 条 Cron 火力线）

| 推送 | Cron ID | 时间 | 内容 | 模式 |
|------|---------|------|------|------|
| 🌅 财务早报 | `5e07746c917a` | 每天 09:00 | 债务全景 + 还款计划追问 + 还款日预警 + 催促发截图 | Agent |
| 📸 暴力催截图 | `7857946435ae` | 每天 10:00, 14:00, 18:00 | 检查昨日微信/支付宝截图是否到位，没发就催 | 脚本(no_agent) |
| 🌙 财务晚报 | `697505ea2288` | 每天 21:00 | 今日还款结果 + 昨日消费小结 + 进度更新 + 还款预警 | Agent |
| 📊 财务周报 | `2e4dfc29dcd8` | 每周日 21:00 | 完整周报：债务+消费+快照+里程碑+Git push | Agent |

- **催收逻辑**：`nag_screenshots.py` 检查 `expenses.json` 的 `screenshots` 数组 → 昨日无数据 → 输出催收消息 → cron 自动推送。已有数据 → 脚本静默退出 → cron 不发任何消息
- **日报包含**：债务进度条 + 还款预警 + 昨日消费（如有）+ 下一里程碑
- **周报包含**：债务周报 + 消费周报 + 快照创建 + Git push

## 核心命令（v2.0）

所有操作通过 Python 脚本完成（禁止手改 JSON）：

```bash
# === 债务 ===
FINANCE_DIR=~/.hermes/adjutant/finance
cd ~/.hermes/adjutant/repo/hermes-adjutant
python3 finance/scripts/finance.py repay -c "花呗" -a 2000
python3 finance/scripts/finance.py update -c "花呗" -a 15446 -s "截图"
python3 finance/scripts/finance.py report --daily
python3 finance/scripts/finance.py report --json
python3 finance/scripts/finance.py daily                   # 综合日报
python3 finance/scripts/finance.py set-duedate -c "花呗" -d 2026-06-10
python3 finance/scripts/finance.py due-check

# === 消费（🆕）===
python3 finance/scripts/expenses.py add -d 2026-06-05 -a 35.50 -m "美团外卖" -s "微信"
python3 finance/scripts/expenses.py batch --items '<JSON>' -s "OCR"
python3 finance/scripts/expenses.py report -t monthly -y 2026 -m 6
python3 finance/scripts/expenses.py summary -d 30
```

## 归途·星火 — 游戏化系统

完整设计文档见 `references/game-system-design.md`。

### 核心文件

| 文件 | 作用 |
|:----|:----|
| `config.json` | 12 座驿站 + 8 个成就（静态定义） |
| `game_state.json` | 运行时状态：已宣布里程碑、已解锁成就、连胜周数、月度记录、事件日志 |

### 归途驿站 — 显示铁律

**每人一灯，各有姓名。** 生成报告/HTML/Telegram消息时：
- 每笔亲友债**独立成行**，绝不归并——16个人就是16行，不能出现"菊仙·陈建·刘小兵 ¥20K×3"
- **姓名先行**：名字是视觉主角，金额和序号退居次要
- **个人注记必显**：`notes` + `since` 字段必须在行内展示
- **高息预警**：利率≥8%用红色标出
- HTML 模板见 `personal-finance` 技能的 `templates/return_starfire.html`

## 🆕 CSV 流水导入（支付宝/微信导出）

波总直接发支付宝或微信导出的 CSV 文件时，使用 `import_csv.py` 自动处理，**不需要 OCR**。

> 详细 CSV 格式参考：`references/csv-import-formats.md`

```bash
# 预览模式（不入库，先看看有多少笔）
python3 finance/scripts/import_csv.py /path/to/alipay.csv --dry-run

# 正式导入
python3 finance/scripts/import_csv.py /path/to/alipay.csv
```

### 自动处理流水线

| 步骤 | 自动完成 |
|------|---------|
| 🔍 平台识别 | 看 CSV 列头自动判断支付宝 vs 微信 |
| 📅 日期解析 | 兼容 `2026-06-01` / `2026/06/01` / `20260601` |
| 🧹 过滤噪音 | 自动跳过：余额宝转入、零钱提现、信用卡还款、基金理财、转账、红包 |
| 🔄 去重 | 按 `日期+金额(取整)+商户名前6字+来源` 去重 |
| 🏷️ 分类 | 17 类规则引擎自动打标 |
| 💾 入库 | 写 expenses.json + 更新 meta |

### 支付宝 CSV 过滤规则
- 跳过：`收/支=收入`、余额宝转入/转出、余利宝、信用卡还款、花呗还款、基金/理财/保险
- 保留：支出类消费

### 微信 CSV 过滤规则
- 跳过：`收/支=收入`、零钱提现、充值、信用卡还款、理财通、微粒贷、转入/转出零钱通
- 跳过：`交易类型=转账/红包/群收款`（这些不算消费）
- 保留：商户消费、扫码付款

### 用户导出指引
- **支付宝**：App → 我的 → 账单 → 右上角 `...` → 开具交易流水证明 → 选择日期 → 导出 CSV
- **微信**：我 → 服务 → 钱包 → 账单 → 右上角 `...` → 下载账单 → 用于个人对账 → 选择日期 → CSV

## 🆕 消费分类默认决策（遇模糊项不打断波总）

当商户名模糊或边缘情况时，按以下默认规则处理，**不反复问波总**：

| 场景 | 默认处理 |
|------|-------------|
| 微信转账给个人 | ❌ 不算消费，导入时自动跳过 |
| 微信红包 | ❌ 不算消费，导入时自动跳过 |
| 支付宝余额宝转入/基金定投 | ❌ 不算消费，导入时跳过 |
| 退款记录 | ✅ 冲抵当日同类别消费 |
| 商户名模糊（XX科技） | 🟡 归「其他」+ 月报中待确认清单 |
| 便利店消费 | 🟢 归「日用」（除非含烟酒关键词→烟酒） |
| 单笔 >¥500 | 🟢 正常归类，月报单独列大额清单 |
| 拼多多/淘宝/京东 | 🟢 归「购物」 |
| 美团/饿了么 | 🟢 归「餐饮」 |
| 滴滴/高德/曹操 | 🟢 归「交通」 |

**核心原则：宁可归入模糊类别事后纠正，也不打断波总节奏反复问。** 月报时列出所有「其他」+「待确认」项，一次性批量确认。

## 陷阱

- **数据文件双重同步（🛑 血坑 — 2026-06-25 再次翻车）**：`~/.hermes/adjutant/finance/`（工作副本）和 `~/.hermes/adjutant/repo/hermes-adjutant/finance/`（Git 仓库）是两套独立目录。**铁律：所有 patch/write 操作直接指向 repo 路径**，不要碰工作副本。如果不小心改了工作副本，必须立即 `cp` + git push。commit 前用 `diff` 检查两副本一致 — 我在 2026-06-25 一次 session 里犯了两次这个错。
- **不要靠 memory/mem0 获取债务数据**——`debts.json` 是单一事实源
- **还款前先 git pull**——其他 AI 可能已更新
- **花呗等平台债金额会波动**——波总发截图时更新 `amount` + `updated_at` + `source`
- **投资款不是债权**——陈春兰投资款、王林投资款等不应出现在 debts.json 中
- **波总维护 Excel（石墨文档）作为原始记录**，系统追踪进度——双轨共存，不冲突
- **归途驿站禁止归并**——每笔亲友债独立成行，禁止合并展示
- **⚠️ Profile 路径解析（血坑）**：在 finance profile 运行时，`~` 和 `HERMES_HOME` 指向 `/Users/mac/.hermes/profiles/finance/home/`，不是真实 home。脚本中需检测 `.hermes/profiles/` 并强制回退到 `/Users/mac`。否则 expenses.json/debts.json 会写入到 profile sandbox 而不是全局工作目录，导致 categories 丢失、数据不可见
- **⚠️ 消费分类为"其他"？** 先检查 expenses.json 的 `categories` 字段是否为空。profile 路径问题会导致加载了空壳文件
- **OCR 引擎优先级（v4.0）**：🥇千问 VL API (dashscope/qwen-vl-max) → 🥈 Apple Vision → 🥉 Tesseract。详见 `debt-screenshot-auto-update` 技能。提取金额后必须波总确认——人眼比 OCR 可靠（度小满 19432→9432，拿去花 5303→9303）
- **📸 支付宝截图 OCR** — 千问 VL 对复杂布局识别明显优于 Apple Vision 和 Tesseract，但支付宝账单仍有一定难度。三引擎都失败时让波总口述
- **截图可以同时更新债务和消费**——先判断截图类型（平台还款页 vs 微信/支付宝账单），走对应管线

## 🚨 网关健康检查与复活

财务中枢依赖独立的 Hermes profile（`finance`），对应 gateway 为 `ai.hermes.gateway-finance`。波总问「财务中枢是不是挂了」时，执行以下检查：

### 快速诊断（30 秒）

```bash
# 1. 查进程
launchctl list | grep gateway-finance
# 正常 → PID 列有值；挂了 → PID 列为 "-"，exit code -9/-15

# 2. 交叉验证（launchctl exit code 是历史值，不可靠）
kill -0 <PID> 2>/dev/null && echo "ALIVE" || echo "DEAD"

# 3. 查防御器
launchctl list | grep defibrillator
tail -3 ~/.hermes/profiles/her-m2/logs/defibrillator.log
```

### 复活步骤

```bash
# 1. 如有端口冲突，先修 config（finance 端口 8646）
launchctl kickstart -k gui/501/ai.hermes.gateway-finance

# 2. 如果防御器也死了，一起复活
launchctl kickstart -k gui/501/com.hermes.defibrillator

# 3. 验证
sleep 5
tail -10 ~/.hermes/profiles/finance/logs/gateway.log | grep -E "Gateway running|Telegram|error"
```

### 常见死因

| 死因 | 症状 | 修复 |
|------|------|------|
| 端口冲突 | 日志满屏 `Port 8642 already in use` | 改端口为 8646（见 `hermes-service-troubleshooting` Mode A2） |
| 防御器先死 → 级联 | defibrillator + gateway 同时消失 | `kickstart -k` 两个都复活 |
| Launchd 崩溃节流 | KeepAlive=true 但不重启 | `kickstart -k` 强制复活 |

详细故障诊断见 `hermes-service-troubleshooting` 技能。
