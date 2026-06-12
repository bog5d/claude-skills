---
name: personal-finance
title: "波总个人财务中枢 v3.1 — 债务 + 消费 + 收入 + 报销四维追踪"
description: "管理波总的亲友债务和平台债务，记录还款，追踪消费（三层账户+子分类+可报销标记），月度收入记录，净现金流分析，游戏化激励。一句话交互：'还了XX N元'。"
trigger: "波总说还款、债务、财务、花呗、借呗、度小满、分付、微粒贷、还钱、还了XX，或要求看债务进度/周报/财报/消费分析/消费流水/深度洞察/收入/报销/净现金流/固定支出/保险分析，或要求整合支付宝微信数据打成JSON，或发来账单截图/平台截图/收入口述/支付宝CSV"
trigger: "波总说还款、债务、财务、花呗、借呗、度小满、分付、微粒贷、还钱、还了XX，或要求看债务进度/周报/财报/消费分析/消费流水/深度洞察，或要求整合支付宝微信数据打成JSON，或发来账单截图"
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
├── expenses.json           ← 消费数据（17类规则引擎 + layer + sub_category + reimbursable）
│ ├── income.json             ← v3.1 收入记录（月度salary/bonus/other_income）
│ ├── recurring.json           ← v3.2 固定支出清单（社保/房租/保险/电话费等）
├── snapshots/YYYY-MM-DD.json  ← 初始 + 周度快照
├── reports/                ← 周报 + 深度分析JSON 生成区
└── scripts/
    ├── finance.py          ← 核心引擎（repay / report --daily / daily / set-duedate / due-check / snapshot / milestones）
    ├── expenses.py         ← v3.1 消费引擎（add / batch / report / recat / summary / screenshot, 三层账户 + 可报销）
    ├── income.py           ← v3.1 收入引擎（log / net / show, 净现金流计算）
    ├── import_csv.py       ← CSV导入器（支付宝/微信CSV → 自动解析+过滤+分类+去重）
    └── nag_screenshots.py  ← 暴力催收脚本（cron no_agent, 检查昨日截图是否到位）
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
波总: 还了分付 500       ← 新增平台债类型
波总: 拿去花清了          ← 等同于还清该笔余额
波总: 花呗清算            ← 同上
波总: [发来微信/支付宝/平台账单截图]  ← 触发 OCR → 自动识别 + 发现新债
```

**处理流程：**
1. 解析债主名 + 金额（"清了"=该笔余额全额）
2. 执行 `python3 ~/.hermes/adjutant/finance/scripts/finance.py repay -c "债主" -a 金额`
3. 读 JSON 输出判断：是否清零、是否触发里程碑
4. 即时反馈：总负债 + 进度条 + 里程碑状态
5. ⚠️ **同步数据 + git push**（scripts 写入 `~/.hermes/adjutant/finance/`，repo 在 `hermes-adjutant/finance/`）：
   ```bash
   # 先同步数据文件到 repo（参见 pitfall #22）
   cp ~/.hermes/adjutant/finance/debts.json ~/.hermes/adjutant/repo/hermes-adjutant/finance/
   cp ~/.hermes/adjutant/finance/transactions.json ~/.hermes/adjutant/repo/hermes-adjutant/finance/
   # 提交
   cd ~/.hermes/adjutant/repo/hermes-adjutant && git add -A && git commit -m "finance: 还XX YY元" && git push
   ```

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
# ── 债务管理 ──
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

# ── 消费追踪 (v3.1 — layer + sub_category + reimbursable) ──
python3 ~/.hermes/adjutant/finance/scripts/expenses.py add -d 2026-06-01 -a 35.50 -m "美团外卖" -s "微信"
python3 ~/.hermes/adjutant/finance/scripts/expenses.py add -d 2026-06-01 -a 2069 -m "龙森园餐饮" --layer business --sub business
python3 ~/.hermes/adjutant/finance/scripts/expenses.py batch --items '<JSON数组>' -s "微信"
python3 ~/.hermes/adjutant/finance/scripts/expenses.py report -t daily|weekly|monthly
python3 ~/.hermes/adjutant/finance/scripts/expenses.py recat E001 -c "商务-招待" --layer business
python3 ~/.hermes/adjutant/finance/scripts/expenses.py recat E005 --sub business  # 仅改子分类

# CSV 导入
python3 ~/.hermes/adjutant/finance/scripts/import_csv.py <文件路径>

# ── 收入追踪 (v3.1) ──
python3 ~/.hermes/adjutant/finance/scripts/income.py log -y 2026 -m 6 -o 14002 -n "妈妈冷秀芳转回"
python3 ~/.hermes/adjutant/finance/scripts/income.py net -y 2026 -m 6   # 净现金流
python3 ~/.hermes/adjutant/finance/scripts/income.py show               # 全部记录
```

## 固定支出追踪（v3.2 — recurring.json）

波总每月刚性固定支出。数据越全，现金流预测越准。波总口述 + 支付宝年度CSV 双重来源。

### 已确认固定项

| 项目 | 金额 | 周期 | 支付方式 |
|------|------|------|----------|
| 👩‍⚕️ 媳妇社保 | ¥2,715 | 每月9日前 | 银行卡 |
| 🏠 房租 | ¥2,600 | 月均（两月一付 ¥5,200） | 银行转账 |
| 📱 电话费 | ¥260 | 每月 | 自动扣 |
| 🛡️ 保险（全家） | ¥1,302 | 月均（多保单分散扣） | 支付宝自动扣 |
| 💰 **合计** | **¥6,877/月** | | |

### 保险明细（由支付宝年度CSV提取）

波总支付宝蚂蚁保 19+ 份保单，覆盖 5 人（*波、**林、**瓅、**汗、**芳），全年 ¥15,627，月均 ¥1,302。

月缴（每笔<¥50）：健康福重疾1号(大病版)×2人、全民保定期寿险、无忧保意外、好医保门诊险、好医保长期医疗
月缴（¥50-150）：好医保长期医疗(0免赔)×3人、好医保住院医疗、健康福重疾(保20/30年)、臻爱定期寿险
月缴（>¥150）：健康福重疾(保1年)、好医保长期医疗(0免赔)-**芳
年缴：车险 川SLG920 ¥2,668（10月）

详细提取脚本见 `references/insurance-policy-analysis.md`

### ⚠️ 重要：保险数据不在 import_csv 结果里

`import_csv.py` 的过滤规则包含「保险」→ 全部被跳过。需要保险数据时必须直接 grep 原始 CSV，不走 import_csv。详见 pitfall #26。

## 三层账户体系（v2.0，基于外部AI分析报告迭代）

每笔消费自动归入四个 layer 之一，月报自动出四层占比：

| Layer | 含义 | 自动归类规则 |
|-------|------|-------------|
| `basic_living` | 基础生活盘 | 餐饮、日用、交通、住房、医疗、数码、娱乐、通讯、保险（默认） |
| `relationship` | 关系责任盘 | 家庭-老婆、家庭-哥哥、家庭-亲属 |
| `event_reserve` | 事件储备盘 | 税费、还款-债务、旅行-酒店 |
| `business` | 经营独立盘 | 经营-代记账、经营-支付网关、经营-公司服务、商务-招待、经营 |

### 餐饮子分类（sub_category）

餐饮自动推断子分类，关键字驱动：

| 子分类 | 触发关键字 |
|--------|-----------|
| `business` | 招待、宴请、商务、客户、龙森园、凯宾斯基、松沪名灶、余家农庄、思见茶苑 |
| `travel` | 火车、高铁、机场、航站楼、服务区、高速、携程、汉庭、亚博 |
| `personal` | 默认（不符合以上任一） |

### 手动覆盖

```bash
# 录入时指定
expenses.py add ... --layer business --sub business

# 事后纠正
expenses.py recat E001 --layer event_reserve
expenses.py recat E005 --sub travel
expenses.py recat E003 -c "商务-招待" --layer business --sub business
```

### 月报输出

`expenses.py report -t monthly` 现在包含 `by_layer` 字段：
```json
{
  "period": "2026-06",
  "total": 5158.98,
  "by_layer": {"basic_living": 5158.98},
  "by_category": {...}
}
```

设计原则：**先跑满3个月数据 → 看真实四层分布 → 再定各层合理阈值**。不要拍脑袋设额度（如"基础生活¥18-20K"），那是另一AI的主观估算，不是实测数据。

## 外部AI报告处理流程

当波总发来外部AI的分析报告（如消费洞察、财务建议）时：

1. **先判断合理部分** — 逐条对照数据验证，区分「洞察」和「建议」
2. **筛选可落地的** — 能自动化的不改行为，能改系统的不改习惯
3. **拒绝主观建议** — 外部AI的金额估算（如"月¥18-20K"）是拍脑袋，必须实测验证
4. **落地到系统** — 合理建议 → expenses.py/finance.py 字段/命令迭代 → git push
5. **汇报边界** — 哪些采纳了、哪些不采纳及原因，必须明确回复波总

⚠️ 外部报告质量参差不齐。好的洞察（如"责任型支出人格""压力来自事件堆叠"）值得参考，但具体金额建议必须跑历史数据反推，不盲从。

## 可报销追踪（v3.1）

差旅/商务消费次月报销（延迟1个月到账）。系统自动标记可报销项，月底生成预估报销额。

### 自动标记规则

以下自动标记为 `reimbursable: true`：

| 触发条件 | 示例 |
|---------|------|
| 旅行-酒店 / 交通-火车票 / 商务-招待 类别 | 汉庭 ¥876、12306 ¥248 |
| 经营-* 类别 | 代记账 ¥3,440 |
| 餐饮 sub_category = business 或 travel | 龙森园 ¥2,069 |
| 商户名含关键词：携程、滴滴、12306、铁路、机票、酒店、凯宾斯基、松沪名灶 | 携程 ¥816、滴滴 ¥50 |

### 月报输出

`expenses.py report -t monthly` 含 `reimbursable` 区块：
```json
{
  "reimbursable": {
    "total": 3662.74,
    "count": 7,
    "items": [...],
    "note": "预估可报销（次月到账），实际以发票为准"
  }
}
```

### 精度说明

- 80-90% 准确。老婆垫付的部分不在波总支付宝/微信数据中，会漏。
- 误标纠正：`expenses.py recat E030 --sub personal`（龙森园是家庭聚餐不是商务）
- 次月报销到账后记收入：`income.py log -o 3663 -n "6月报销到账"`

## 收入追踪（v3.1）

粗颗粒度月收入记录。波总每月口述一句即可。

### 波总收入结构（深度记忆）

- 长沙公司月薪 ~¥20,000
- 广州公司月薪 ~¥10,000
- 年度奖金 ¥100,000-150,000（月均摊 ~¥10,400）
- 其他工作外收入 → 打入妈妈（冷秀芳）银行卡 → 妈妈微信转回
- **冷秀芳 = 妈妈**，不是借款关系。她转回的是波总自己的其他收入
- 月收入粗估 ¥40,000-50,000+

### 额外流出（未在支付宝/微信体现）

- 每月银行卡转老婆 Dily ~¥20,000+（家庭支配 + 还债，偶尔周转回来）
- 支付宝/微信另有 ~¥5,000/月流向老婆（布尔乔亚商户）
- 老婆总流向 ~¥25,000/月

### CLI

```bash
# 记录其他收入（妈妈转回、报销到账等）
income.py log -y 2026 -m 6 -o 14002 -n "妈妈转回"

# 净现金流 = 收入 - 消费 + 预估报销
income.py net -y 2026 -m 6
# → {"income": 54402, "expenses": 5158.98, "reimbursable_estimate": 3662.74, "net_after_reimburse": 52905.76}
```

净现金流公式：`net_after_reimburse = income - expenses + reimbursable_estimate`

正数 = 有盈余，负数 = 当月透支。不追求精确，粗颗粒度趋势判断。

### 两条输入通道

| 通道 | 触发方式 | 处理引擎 |
|------|---------|---------|
| 📸 截图 | 波总发微信/支付宝账单截图 | 千问 VL API（首选）→ Apple Vision（降级）→ expenses.py batch |
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

每次还款即时处理：先 `cp` 数据文件到 repo 再 `git commit + push`（不等 cron，参见 pitfall #22）。

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
10. **⚠️ Profile 路径陷阱（两态都要防）** — finance.py 用 `os.environ.get("HERMES_HOME", os.path.expanduser("~"))` 解析 home。两种错误态：
    - **态A（交互会话）**: `HERMES_HOME` = `~/.hermes/profiles/<name>/home/` → 脚本内 `".hermes/profiles/" in str(_HOME)` 检测命中 → 自动修正。✅ 已有防护
    - **态B（Cron 会话）**: `HERMES_HOME` = `/Users/mac/.hermes`（顶层 hermes 目录，不含 `profiles/`）→ 检测**不命中** → `FINANCE_DIR` 变成 `/Users/mac/.hermes/.hermes/adjutant/finance/`（双重 `.hermes`）→ FileNotFoundError。❌ 无防护
    - **态B 解法**: Cron job 中运行 finance.py 前必须显式设置 `HERMES_HOME=/Users/mac FINANCE_DIR=/Users/mac/.hermes/adjutant/finance`。不要依赖脚本内的自动检测。态B 的 `$HOME` 正确（`/Users/mac`）但 `HERMES_HOME` 覆盖了它。症状是路径中出现双重 `.hermes`
11. **支付宝 CSV 编码** — 支付宝导出的 CSV 是 **GBK** 编码，不是 UTF-8。需先 `iconv -f GBK -t UTF-8` 转换再处理
12. **CSV 日期范围** — 微信账单导出时注意终止时间要选当前日期，否则会漏掉最近几天的数据
13. **截图 vs CSV 优先级** — 同一笔交易 CSV 的商户名更准确（截图 OCR 可能误读"明红蹄花"的供应商名），优先保留 CSV 版本
14. **分类关键字自动学习** — 每次发现新的商户名模式（如"蹄花""龙森园""相思椒"），立即追加到 `expenses.json` 的 categories 关键字库。⚠️ **batch 导入后必须检查**：`grep '"其他"' expenses.json` 找出被归入"其他"的项 → recat 纠正 → 把商户关键字补入 `expenses.json` 的 categories 字段。已知常被误归"其他"的商户：DeepSeek API→经营-软件服务、阿里云→经营-软件服务、顺丰→日用-快递、享道出行→交通、安徽蒸小碗/XX蹄花/XX小碗→餐饮、直豆→娱乐、湖南计算智谷/XX物业→交通-停车、App Store/Apple Music→数码
15. **JSON输出类型混淆** — 波总说"打成JSON"时若上下文中提到"消费流水""深度分析""洞察"，必须出 `consumption_deep_analysis.json`（类型一），不要出 `bog_finance_portrait_handoff.json`（类型二）。类型一是深度洞察，类型二是全景快照。判断标准：看波总是否在讨论消费数据。
16. **Layer 默认值** — 新录入的消费默认 layer 为 `basic_living`。商务招待/经营相关必须在录入时手动指定 `--layer business`，或事后 `expenses.py recat` 纠正。
17. **外部AI金额建议不盲从** — 外部报告提出的具体金额阈值（如"月¥18-20K"）是主观估算，不是实测数据。必须先跑满3个月 layer 分布再定阈值，不要直接写入系统配置。
18. **⚠️ Cron 脚本路径陷阱（no_agent 模式）** — `no_agent=true` 的 cron job 使用相对路径 `script` 时，解析到 profile 的 `scripts/` 目录（如 `~/.hermes/profiles/finance/scripts/`），不是 adjutant 的 `finance/scripts/`。必须把脚本复制到 profile scripts 目录才能被 cron 找到：`cp ~/.hermes/adjutant/finance/scripts/nag_screenshots.py ~/.hermes/profiles/finance/scripts/`。这和 pitfall #10 的 `expanduser` 陷阱是不同的路径解析问题。
19. **平台债类型发现** — 系统当前追踪 4 种平台债（花呗/拿去花/度小满/工行贷款），但截图可能暴露未追踪的新平台债（如微信分付、借呗、微粒贷等）。遇到截图中的还款记录但 creditor 不在 debts.json 中时，必须主动询问波总总余额和还款日，不要默默忽略。
20. **分付特殊处理** — 微信分付是 ¥4,000 额度、18-20% 利率的临时周转工具。波总用完即填（6/6 还款 ¥479.22 已清零）。**不加入 debts.json**（非固定债），但作为高风险工具备忘。铁律：绝不让分付滚到下个账单周期。其他类似 revolving credit 同理。
21. **截图 OCR 管线（v4.0，2026-06-12 波总指定优先级）** — 引擎优先级：🥇千问 VL API (dashscope/qwen-vl-max) → 🥈 Apple Vision (Swift) → 🥉 Tesseract (`chi_sim`)。详见 `debt-screenshot-auto-update` 技能的 "OCR 引擎" 章节。
22. **数据文件双重同步** — `~/.hermes/adjutant/finance/` 和 `~/.hermes/adjutant/repo/hermes-adjutant/finance/` 是两个独立目录。`finance.py`/`expenses.py` 写入前者，git 仓库是后者。每次数据修改后必须 `cp` 到 repo 再 commit+push。漏 sync 会导致 git push 只提交了旧版本。
26. **⚠️ import_csv 过滤掉了保险 — 需要保险数据时直接 grep CSV** — `import_csv.py` 的过滤规则明确跳过「保险」类别（归入理财/保险过滤）。当波总需要分析保险支出时，必须在解压支付宝 ZIP（GBK 编码）→ `iconv -f GBK -t UTF-8` 转码后，直接用 `grep -i "保险"` 从原始 CSV 提取，不要走 import_csv。提取流程见 `references/insurance-policy-analysis.md`。
27. **支付宝 ZIP 解压编码问题** — 支付宝导出的 ZIP 文件名含中文，Windows 端创建导致编码不兼容。`unzip -P <密码>` 可能报 `Illegal byte sequence`。优先用 Python `zipfile` 模块：`zf.setpassword(b'密码')` + `zf.extract()` 可绕开中文文件名编码问题。
23. **⚠️ Git pull 快照冲突（多 AI 并行）** — 本地 `snapshots/YYYY-MM-DD.json` 为 untracked 文件，远程已有同名文件时 `git pull` 报错：`error: untracked working tree files would be overwritten by merge`。解法：`rm -f finance/snapshots/YYYY-MM-DD.json && git pull origin main`。根本原因是周报 cron 创建的本地 snapshot 未 add+commit 就被其他 agent push 的同名文件阻塞。
24. **⚠️ Cron `cd` 路径解析** — Cron 会话中 `cd ~/.hermes/...` 的 `~` 被 profile 覆盖，解析到 profile sandbox（如 `/Users/mac/.hermes/profiles/finance/home/.hermes/...`）。所有 `cd` 和相对路径必须改用绝对 `/Users/mac/...`。关联 pitfall #10（态B）。
25. **⚠️ Batch 去重误杀：同日同金额段交易** — `expenses.py batch` 去重逻辑为 `日期相同 + 金额差≤¥2 + 商户名相似度>0.5`。同品类同日相近金额会被误判。**真实案例**：6/8 滴滴快车-宋师傅 ¥18.90 被误判为 滴滴专车-袁师傅 ¥19.00 的重复（similarity 0.75），实际是两笔独立行程。**解法**：确认非真重复后，用 `python3 -c` 手动追加到 expenses.json 再 cp+push。常见误杀场景：滴滴×N、美团外卖×N、同一商户多笔近距离消费。手动插入模板：
    ```bash
    python3 -c "
    import json; p='/Users/mac/.hermes/adjutant/finance/expenses.json'
    with open(p) as f: d=json.load(f)
    d['expenses'].append({'id':f'E{len(d[\"expenses\"])+1:03d}','date':'...','amount':...,'merchant':'...','category':'...','layer':'basic_living','source':'支付宝','dedup_key':'...','created_at':'...','reimbursable':True})
    d['meta']['total_expenses']=len(d['expenses']); d['meta']['total_amount']=round(sum(e['amount'] for e in d['expenses']),2)
    with open(p,'w') as f: json.dump(d,f,ensure_ascii=False,indent=2)
    "
    ```
26. **⚠️ import_csv 过滤掉了保险 — 需要保险数据时直接 grep CSV** — `import_csv.py` 的过滤规则明确跳过「保险」类别（归入理财/保险过滤）。当波总需要分析保险支出时，必须在解压支付宝 ZIP（GBK 编码）→ `iconv -f GBK -t UTF-8` 转码后，直接用 `grep -i \"保险\"` 从原始 CSV 提取，不要走 import_csv。提取流程见 `references/insurance-policy-analysis.md`。
27. **支付宝 ZIP 解压编码问题** — 支付宝导出的 ZIP 文件名含中文，Windows 端创建导致编码不兼容。`unzip -P <密码>` 可能报 `Illegal byte sequence`。优先用 Python `zipfile` 模块：`zf.setpassword(b'密码')` + `zf.extract()` 可绕开中文文件名编码问题。
    python3 -c "
    import json; p='/Users/mac/.hermes/adjutant/finance/expenses.json'
    with open(p) as f: d=json.load(f)
    d['expenses'].append({'id':f'E{len(d[\"expenses\"])+1:03d}','date':'...','amount':...,'merchant':'...','category':'...','layer':'basic_living','source':'支付宝','dedup_key':'...','created_at':'...','reimbursable':True})
    d['meta']['total_expenses']=len(d['expenses']); d['meta']['total_amount']=round(sum(e['amount'] for e in d['expenses']),2)
    with open(p,'w') as f: json.dump(d,f,ensure_ascii=False,indent=2)
    "
    ```
