---
name: personal-finance
title: "波总个人财务中枢 — 债务追踪 + 游戏化还款"
description: "管理波总的亲友债务和平台债务，记录还款，生成周报，游戏化激励。一句话交互：'还了XX N元'。"
category: user-patterns
trigger: "波总说还款、债务、财务、花呗、借呗、度小满、还钱、还了XX，或要求看债务进度/周报/财报/消费分析/消费流水/深度洞察，或要求整合支付宝微信数据打成JSON"
---

# 波总个人财务中枢

## 概述

独立于副官任务管理的第二个职能模块。核心目的：**让波总对债务全景一目了然，让还款上瘾。**

设计原则：
- **零表单** — 波总一句话 `还了花呗2000` 即完成记录
- **游戏化** — 里程碑Boss + 成就徽章 + 进度条
- **每周推送** — 周日晚自动生成全景大盘
- **数据双轨** — Excel 记详细成因（波总维护），系统追踪金额进度（自动）

## 数据文件

```
~/.hermes/adjutant/finance/
├── debts.json              ← 债务主数据（active + cleared 列表）
├── config.json             ← 里程碑阈值 + 成就定义
├── transactions.json       ← 还款流水 [{date, creditor, amount, ...}]
├── expenses.json           ← 🆕 消费数据（17类规则引擎 + 截图追踪）
├── snapshots/YYYY-MM-DD.json  ← 初始 + 周度快照
├── reports/                ← 周报生成区
└── scripts/
    ├── finance.py          ← 核心引擎（repay / report --daily / daily / set-duedate / due-check / snapshot / milestones）
    ├── expenses.py         ← 🆕 消费追踪引擎（add / batch / report / recat / summary / screenshot）
    ├── import_csv.py       ← 🆕 CSV导入器（支付宝/微信CSV → 自动解析+过滤+分类+去重）
    └── nag_screenshots.py  ← 🆕 暴力催收脚本（cron 用，检查昨日截图是否到位）
```

**GitHub 双副本**：`hermes-adjutant/finance/`（和副官同一仓库）。每次变更 git push，任何 AI 可通过 `git pull` 接盘。

### debts.json 结构

```json
{
  "meta": {
    "total_active_family": 460650,
    "total_active_platform": 64612.39,
    "grand_total": 525262.39,
    "total_cleared": 210000,
    "milestones": [500000, 450000, ...]
  },
  "active": [
    {
      "id": "F001",
      "creditor": "妈妈",
      "type": "亲友",
      "amount": 135100,
      "rate": 0.047,
      "notes": "",
      "since": "2018-04"
    }
  ],
  "cleared": [
    {
      "id": "C001",
      "creditor": "老姚达州",
      "type": "亲友",
      "original": 150000,
      "rate": 0.084,
      "notes": "🏆 最大一笔"
    }
  ]
}
```

`type` 字段：`亲友` | `平台`

## 交互模型

### 记录还款
波总说一句话，自动识别债主和金额：

```
波总: 还了花呗 2000
波总: 还了妈妈 5000
波总: 拿去花清了          ← 等同于还清该笔余额
波总: 花呗清算            ← 同上
```

**处理流程：**
1. 解析债主名 + 金额（"清了"=该笔余额全额）
2. 执行 `python3 ~/.hermes/adjutant/finance/scripts/finance.py repay -c "债主" -a 金额`
3. 读 JSON 输出判断：是否清零、是否触发里程碑
4. 即时反馈：总负债 + 进度条 + 里程碑状态
5. ⚠️ **必须 git commit + push**（`cd ~/.hermes/adjutant/repo/hermes-adjutant && git add -A && git commit -m "finance: 还XX YY元" && git push`）

### 查询债务
```
波总: 我的债务 / 债务进度 / 还欠多少
```

返回：总负债 + 分类 + 进度条 + 里程碑路线 + 利率排序（高息优先）

### 还款建议
```
波总: 下个月能还8000，先还哪个
```

按利率从高到低排序，推荐优先清高息债务。

## 游戏化系统

### 里程碑（Boss战）

| 阈值 | 名称 | 图标 |
|------|------|------|
| ¥521,262 | 起点：知己知彼 | 🗺️ |
| ¥500,000 | 突破50万大关 | ⚔️ |
| ¥450,000 | 新的基准线 | 🛡️ |
| ¥400,000 | 进入40万区间 | 🏹 |
| ¥350,000 | 过半征程 | 🔥 |
| ¥300,000 | 轻装前进 | 💨 |
| ¥250,000 | 黎明前夕 | 🌅 |
| ¥200,000 | 风暴之眼 | 👁️ |
| ¥150,000 | 最后的堡垒 | 🏰 |
| ¥100,000 | 进入决战区 | ⚡ |
| ¥50,000 | 胜利在望 | 🎯 |
| ¥0 | Zero Day | 👑 |

每次突破里程碑 → 庆祝消息 + 历史对比 + 距下一Boss预测。

### 成就徽章

| 成就 | 条件 |
|------|------|
| 🩸 第一滴血 | 第一笔还款 |
| 💀 首杀 | 清掉第一笔债 |
| 🔥 五连杀 | 清掉5笔债 |
| ⚔️ 家族副本过半 | 亲友债还掉50% |
| 📱 平台清零 | 所有平台债清零 |
| ⛓️ 连续作战 | 连续4周有还款 |
| 🛡️ 铁血纪律 | 连续12周有还款 |
| 🏆 月度MVP | 单月还款创纪录 |

## 周报格式

每周日晚自动推送，一张大盘图：

```
📊 波总财务周报 | YYYY年第W周

💰 本周还款：¥X,XXX
📉 当前总负债：¥XXX,XXX
   较上周：↓ ¥X,XXX
   较上月同期：↓ ¥XX,XXX

🗓️ 按近4周均速 ¥X,XXX/周
   预计清债日：YYYY年M月（约N周）

📈 进度条
███████░░░░░░░░░░░░  28.4%

🏆 里程碑
   ✅ 已达成 ...
   ⏳ 下一个Boss：¥XXX,XXX（还差 ¥X,XXX）

🎯 高息债优先
   1. XX ¥XX,XXX  X%
   2. ...

💀 本周击杀
   已清：XX ¥X,XXX
```

## 核心命令

所有操作通过 `finance.py` 完成（不要手改 JSON）：

```bash
# 记录还款
python3 ~/.hermes/adjutant/finance/scripts/finance.py repay -c "花呗" -a 2000

# 生成报告
python3 ~/.hermes/adjutant/finance/scripts/finance.py report          # 完整周报
python3 ~/.hermes/adjutant/finance/scripts/finance.py report --daily  # 日报（精简）
python3 ~/.hermes/adjutant/finance/scripts/finance.py report --json   # JSON 输出
python3 ~/.hermes/adjutant/finance/scripts/finance.py daily           # 综合日报（债务+消费+预警）

# 还款日管理
python3 ~/.hermes/adjutant/finance/scripts/finance.py set-duedate -c "花呗" -d "2026-06-10"
python3 ~/.hermes/adjutant/finance/scripts/finance.py due-check       # 检查未来5天到期

# 快照 & 里程碑
python3 ~/.hermes/adjutant/finance/scripts/finance.py snapshot
python3 ~/.hermes/adjutant/finance/scripts/finance.py milestones

# 消费追踪
python3 ~/.hermes/adjutant/finance/scripts/expenses.py add -d 2026-06-01 -a 35.50 -m "美团外卖" -s "微信"
python3 ~/.hermes/adjutant/finance/scripts/expenses.py batch --items '<JSON数组>' -s "微信"
python3 ~/.hermes/adjutant/finance/scripts/expenses.py report -t daily|weekly|monthly
python3 ~/.hermes/adjutant/finance/scripts/expenses.py recat <ID> <新类别>

# CSV 导入
python3 ~/.hermes/adjutant/finance/scripts/import_csv.py <文件路径>
```

## 消费追踪子系统（v2.0）

### 两条输入通道

| 通道 | 触发方式 | 处理引擎 |
|------|---------|---------|
| 📸 截图 | 波总发微信/支付宝账单截图 | Apple Vision OCR → 逐笔提取 → expenses.py batch |
| 📎 CSV | 波总发导出文件（支付宝CSV是GBK编码，微信是xlsx） | import_csv.py 自动解析 |

### 消费过滤规则（自动排除）

以下**不算消费**，`import_csv.py` 自动跳过：

- 转账给个人 / 微信红包
- 余额宝转入 / 基金定投 / 支付宝小荷包
- 信用卡还款 / 分付还款 / 零钱提现
- 个人所得税 / 缴税
- 退款记录（金额为负时单独标记）

### 去重策略

1. **常规去重**（expenses.py `add_expense`）：`日期 + 金额(±2元) + 商户名相似度 > 0.5`
2. **CSV vs 截图去重**：同一笔交易的商户名可能不同（如截图OCR"火车票" vs CSV"携程旅行网"），需要手动检查
3. **跨天重复截图**：已入库的日期范围内自动标记 duplicate

### 分类引擎

17 个类别，关键字库存储在 `expenses.json` → `categories` 字段。每次导入后自动扩充关键字。

### 不确定项 — 处理原则

遇到模糊商户名（如"布尔乔亚(余玓瓅)"）或分类边界模糊时：
- 归入「其他」类，月报生成时汇总问波总
- **不打断交互节奏**，宁可事后纠正

## 自动化

财务中枢运行在独立 Gateway（profile `finance`，bot `@BogFinance_bot`），**四条** cron 推送线：

| 推送 | 时间 | 内容 |
|------|------|------|
| 🌅 早报 | 每天 09:00 | 债务全景 + 还款计划追问 + 消费数据检查 |
| 📸 催截图 | 每天 10:00 / 14:00 / 18:00 | 检查昨日微信/支付宝账单截图是否到位，缺就催 |
| 🌙 晚报 | 每天 21:00 | 今日还款 + 昨日消费 + 还款预警 + 游戏化鼓励 |
| 📊 周报 | 每周日 21:00 | 完整周报 + 快照 + Git push |

### 催截图机制

`scripts/nag_screenshots.py` 通过 cron 以 `no_agent=true` 模式每 4 小时运行一次（10:00、14:00、18:00）。检查 `expenses.json` 的 `meta.last_screenshot_date` — 如果不是昨天 → 输出催收消息（空输出 = 静默，不推送）。超过 3 次会追加语气加重的消息。

每次还款即时处理：`git commit + push`（不等 cron）。

### 部署架构

```
@BogFinance_bot（独立 Telegram bot）
    ↕
finance profile Gateway（launchd: ai.hermes.gateway-finance）
    ↕
personal-finance skill + ~/.hermes/adjutant/finance/ 数据
    ↕
GitHub: hermes-adjutant/finance/（双副本，AI 可接盘）
```

与副官是**平行独立线**——副官管工程/任务/研究，财务 Bot 只管钱。故障互不传染。

## 归途驿站 — 显示铁律

**核心理念：每人一灯，各有姓名。** 归途的意义在于还的不是"一笔债"，是**那个具体的人**。

展示规则：
- **每笔亲友债独立成行**，禁止归并、分组、压缩——16个人就是16行
- **姓名先行**：名字是视觉主角（金色/星色，加粗），金额和排位退居次要
- **个人注记必显**：`notes` 字段（"借于2018-04""借钱买车的保险"等）、`since` 字段（借款时间）必须在行内展示
- **高息预警**：利率 ≥8% 用红色标注，提醒优先清
- **排位号缩微**：只起索引作用，不抢名字的视觉权重
- **已清驿站（星火墙）**：每人一个 badge，传奇级（≥¥100K）用✨+特殊样式

HTML 原型模板：`~/.hermes/cache/documents/return_starfire_v2.html`
样式暗黑主题（`--bg: #0d0f18`），深色卡布局，金色暖色系。

## JSON 输出与 AI 交接

当波总要求"打成 JSON 给另一个 AI 接盘"时，需区分两种输出类型：

### 类型一：消费流水深度分析（优先）

**触发词**：消费流水、深度分析、洞察、整合支付宝微信、过去一年消费

产物：`reports/consumption_deep_analysis.json`（10 维结构，~19K chars）

包含：overview / category_ranking / monthly_trend / relationship_flows / business_flows / top_merchants / deep_insights / recommendations / current_month / debt_context

**铁律**：波总说"整合消费数据"→ 直接出深度分析，不要混债务数据。分析要有洞察（收入画像、消费模式、出差指纹、风险信号），不是数据罗列。

### 类型二：完整财务画像（含债务）

**触发词**：全部数据、完整 JSON、财务全景、另一 AI 接盘（无"消费"关键词）

产物：`reports/bog_finance_portrait_handoff.json`

包含：subject + debt(全量) + consumption(摘要) + game_state + meta_context

### ⚠️ 区分陷阱

- 波总说"把数据打成 JSON"但上下文在讨论消费流水 → 出类型一，不是类型二
- 波总说"深度洞察和分析" → 必须出类型一，类型二不够
- 不确定时：先问"要消费深度分析还是全量财务画像？"，不要猜

详细 JSON schema 见 `references/consumption-analysis-schema.md`

## 陷阱

1. **不要手改 JSON，用 finance.py / expenses.py** — 脚本已处理元数据更新、去重、清债转移、交易记录
2. **每次还款后必须 git push** — 立即 `cd hermes-adjutant && git add -A && git commit && git push`
3. **债主名精确匹配** — 用 `-c "花呗"` 精确匹配 creditor 字段，不支持模糊
4. **不要把财务消息当副官任务** — "还了花呗2000"是财务指令，不是创建任务
5. **利率为空** — 大部分亲友债无利率，排序时 null 排最后
6. **已清债主重名** — 已清列表和活跃列表分开，匹配只查 active
7. **金额超额保护** — finance.py 自动 cap 到 0，超额的差额会提示
8. **Excel 双轨不同步** — 以波总口头确认为准，Excel 是历史参考
9. **归途驿站禁止归并** — 每笔亲友债必须独立一行
10. **⚠️ Profile 路径陷阱** — Hermes profile 的 `HOME` 环境变量指向 `~/.hermes/profiles/<name>/home/`，导致 `os.path.expanduser("~")` 解析到沙盒路径。finance.py 和 expenses.py 已内置检测：检测到 `.hermes/profiles/` 在路径中时，强制使用 `/Users/mac` 作为真实 home
11. **支付宝 CSV 编码** — 支付宝导出的 CSV 是 **GBK** 编码，不是 UTF-8。需先 `iconv -f GBK -t UTF-8` 转换再处理
12. **CSV 日期范围** — 微信账单导出时注意终止时间要选当前日期，否则会漏掉最近几天的数据
13. **截图 vs CSV 优先级** — 同一笔交易 CSV 的商户名更准确（截图 OCR 可能误读"明红蹄花"的供应商名），优先保留 CSV 版本
14. **分类关键字自动学习** — 每次发现新的商户名模式（如"蹄花""龙森园""相思椒"），立即追加到 `expenses.json` 的 categories 关键字库
15. **JSON输出类型混淆** — 波总说"打成JSON"时若上下文中提到"消费流水""深度分析""洞察"，必须出 `consumption_deep_analysis.json`（类型一），不要出 `bog_finance_portrait_handoff.json`（类型二）。类型一是深度洞察，类型二是全景快照。判断标准：看波总是否在讨论消费数据。
