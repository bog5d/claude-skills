---
name: finance-hub
description: 波总个人财务中枢 v2.0 — 债务追踪 + 消费分析 + 还款日预测 + 暴力催收。当你收到"还了XX YY元""花呗清了""我的债务""截图""消费"等财务相关指令时使用。
category: productivity
trigger: 还了|还款|债务|负债|花呗|借呗|还款进度|财务|欠款|清债|消费|截图|账单|支付宝|微信账单|报销|基金
---

# 财务中枢 (Finance Hub)

波总的个人债务/还款追踪系统，独立于副官任务管理之外的第二个职能模块。

## 文件位置

```
~/.hermes/adjutant/finance/          ← 本地工作目录
~/.hermes/adjutant/repo/hermes-adjutant/finance/  ← Git 仓库（单一事实源）
```

| 文件 | 用途 |
|------|------|
| `debts.json` | 全部债务：`active`（待还）+ `cleared`（已清）+ `meta` |
| `config.json` | 12 个里程碑 + 8 个成就定义 |
| `transactions.json` | 还款流水（每条一笔记录） |
| `snapshots/YYYY-MM-DD.json` | 每周自动快照 |
| `scripts/finance.py` | 核心引擎（repay / report / daily / snapshot / milestones / set-duedate / due-check） |
| `scripts/expenses.py` | 🆕 消费追踪引擎（add / batch / report / summary / recat / screenshot） |
| `scripts/nag_screenshots.py` | 🆕 暴力催收脚本（检查昨日截图到位否，没到位输出催收消息） |
| `expenses.json` | 🆕 消费数据 + 17 类别规则引擎 + 截图记录 |

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

## 归途驿站 — 显示铁律

**每人一灯，各有姓名。** 生成报告/HTML/Telegram消息时：
- 每笔亲友债**独立成行**，绝不归并——16个人就是16行，不能出现"菊仙·陈建·刘小兵 ¥20K×3"
- **姓名先行**：名字是视觉主角，金额和序号退居次要
- **个人注记必显**：`notes` + `since` 字段必须在行内展示
- **高息预警**：利率≥8%用红色标出
- HTML 模板见 `personal-finance` 技能的 `templates/return_starfire.html`

## 陷阱

- **不要靠 memory/mem0 获取债务数据**——`debts.json` 是单一事实源
- **还款前先 git pull**——其他 AI 可能已更新
- **花呗等平台债金额会波动**——波总发截图时更新 `amount` + `updated_at` + `source`
- **投资款不是债权**——陈春兰投资款、王林投资款等不应出现在 debts.json 中
- **波总维护 Excel（石墨文档）作为原始记录**，系统追踪进度——双轨共存，不冲突
- **归途驿站禁止归并**——每笔亲友债独立成行，禁止合并展示
- **⚠️ Profile 路径解析（血坑）**：在 finance profile 运行时，`~` 和 `HERMES_HOME` 指向 `/Users/mac/.hermes/profiles/finance/home/`，不是真实 home。脚本中需检测 `.hermes/profiles/` 并强制回退到 `/Users/mac`。否则 expenses.json/debts.json 会写入到 profile sandbox 而不是全局工作目录，导致 categories 丢失、数据不可见
- **⚠️ 消费分类为"其他"？** 先检查 expenses.json 的 `categories` 字段是否为空。profile 路径问题会导致加载了空壳文件
- **OCR 提取金额后必须波总确认**——人眼比 OCR 可靠（度小满 19432→9432，拿去花 5303→9303）
- **截图可以同时更新债务和消费**——先判断截图类型（平台还款页 vs 微信/支付宝账单），走对应管线
