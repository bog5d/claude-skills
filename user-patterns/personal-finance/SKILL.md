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
    ├── nag_screenshots.py  ← 暴力催收脚本（cron no_agent, 检查昨日截图是否到位）
    └── audit_consistency.py ← 13 项一致性审计（详见 scripts/ 说明）
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

`type` 字段：`亲友` | `平台` | `其他`（自债，如 I001 基金储备占用）

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

> 完整设计文档见 `finance-hub` 技能的 `references/game-system-design.md`。<br>
> 运行时状态追踪文件：`debts.json` 同级目录下的 `game_state.json`。

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

# ── 审计 (v3.3) ──
# 13 项一致性检查：debts meta vs 求和 / tx 引用 / config 对齐 / game_state / 快照 / expenses 内部 / 双副本同步
# 从技能目录复制到 finance/scripts/ 后运行：
#   cp ~/.hermes/profiles/finance/skills/user-patterns/personal-finance/scripts/audit_consistency.py ~/.hermes/adjutant/finance/scripts/
#   cd ~/.hermes/adjutant/repo/hermes-adjutant
#   python3 finance/scripts/audit_consistency.py          # 检查模式
#   python3 finance/scripts/audit_consistency.py --fix    # 自动修复 + push
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

### 批量 Layer 推断（旧数据回填）

当发现大量旧记录缺 layer 字段时，按以下规则批量推断（`python3 -c` 直接操作 expenses.json）：

| 推断依据 | 目标 layer | 示例 |
|---------|-----------|------|
| category ∈ {餐饮,餐饮美食,交通,交通出行,日用,购物,住房,医疗,通讯,教育,烟酒,娱乐,数码,快递,加油,停车,理发,储物,车位,买菜,水电,高速通行,休闲/足道,AI服务} | `basic_living` | 美团 ¥62 → basic_living |
| category ∈ {母婴,人情,人情往来,红包} | `relationship` | 红包 ¥560 → relationship |
| category ∈ {旅行,预存,保险} | `event_reserve` | 携程 ¥410 → event_reserve |
| category ∈ {经营-软件服务,茶叶/商务} | `business` | 龙森园 ¥2,069 → business |
| 商户名含关键字 ∈ {龙森园,凯宾斯基,松沪名灶,招待,宴请,客户,代记账,公司} | `business` | 覆盖 category 默认推断 |
| 商户名含关键字 ∈ {媳妇,老婆,Dily,余玓瓅,布尔乔亚} | `relationship` | 覆盖 category 默认推断 |
| category ∈ {理财,分付还款,二维码收款,红包,转账,转账-妈妈,转账-李杰,转账-nevis} | 非消费，跳过不移入 | 余额宝 ¥1.88 → skip |

批量推断脚本模板：
```python
import json
from pathlib import Path
p = Path('/Users/mac/.hermes/adjutant/finance/expenses.json')
with open(p) as f: ex = json.load(f)

basic_living_cats = {'餐饮','餐饮美食','交通','交通出行','日用','购物','住房','医疗','通讯','教育','烟酒','娱乐','数码','快递','加油','停车','理发','储物','车位','买菜','水电','高速通行','休闲/足道','AI服务'}
relationship_cats = {'母婴','人情','人情往来','红包'}
event_reserve_cats = {'旅行','预存','保险'}
business_cats = {'经营-软件服务','茶叶/商务'}
skip_cats = {'理财','分付还款','二维码收款','红包','转账','转账-妈妈','转账-李杰','转账-nevis'}
merchant_biz = ['龙森园','凯宾斯基','松沪名灶','招待','宴请','客户','代记账','公司']
merchant_rel = ['媳妇','老婆','Dily','余玓瓅','布尔乔亚']

for e in ex['expenses']:
    if e.get('layer') in ('basic_living','relationship','event_reserve','business'): continue
    if e.get('category','') in skip_cats: continue
    m = e.get('merchant','')
    if any(kw in m for kw in merchant_biz): e['layer']='business'
    elif any(kw in m for kw in merchant_rel): e['layer']='relationship'
    elif e['category'] in relationship_cats: e['layer']='relationship'
    elif e['category'] in event_reserve_cats: e['layer']='event_reserve'
    elif e['category'] in business_cats: e['layer']='business'
    elif e['category'] in basic_living_cats: e['layer']='basic_living'
    else: e['layer']='basic_living'  # 兜底

ex['meta']['total_amount'] = round(sum(e['amount'] for e in ex['expenses']), 2)
with open(p, 'w') as f: json.dump(ex, f, ensure_ascii=False, indent=2)
```

⚠️ **执行后必须**：cp 同步到 repo + git push + 运行 `audit_consistency.py` 验证 layer 完整性（项 6）。

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

### 财务全景诊断

当波总要求「分析财务状况」「做诊断」时，使用 `references/financial-diagnosis-framework.md` 的结构输出。核心原则：实时数据驱动、一个方案不要选择题、老婆支出标注为总包。

### 波总收入结构（深度记忆）

- 长沙公司月薪 ~¥20,000
- 广州公司月薪 ~¥10,000
- 年度奖金 ¥100,000-150,000（月均摊 ~¥10,400）
- 其他工作外收入 → 打入妈妈（冷秀芳）银行卡 → 妈妈微信转回
- **冷秀芳 = 妈妈**，不是借款关系。她转回的是波总自己的其他收入（主要是**去年奖金分期发放**，¥5,000~¥10,000/月不等）
- ⚠️ 银行流水中的「代发款项」是总包，含月薪+报销+绩效补充。月薪固定部分约¥20K/月（长沙公司），报销和补充随出差多少波动
- 月收入粗估 ¥40,000-50,000+
- ⚠️ **银行流水中的「工资」含报销/差旅费/绩效补充** — 银行「代发款项」是一个总包，不分工资和报销。当显示「银行流水¥46K」时，其中月薪固定部分约¥20K，余下为报销和补充。不要将银行流水数额等同于「纯工资」。

### 额外流出（未在支付宝/微信体现）

- 每月银行卡转老婆 Dily ~¥20,000+（家庭支配 + 还债，偶尔周转回来）
- 支付宝/微信另有 ~¥5,000/月流向老婆（布尔乔亚商户）
- 老婆总流向 ~¥25,000/月

### 老婆信用卡债务追踪

Dily 的信用卡已纳入 debts.json 追踪（`type="平台"`，creditor 前缀「老婆-」）。当波总发来 Dily 信用卡截图时：

1. **录入 debts.json** — 创建 P005+ 独立条目，creditor=`老婆-XX银行`
2. **总欠款分析** — 截图通常分三块：本期未还 / 下期待还 / 分期剩余 → 总欠款 = 三者之和
3. **还款日追踪** — 在 `due_date` 字段标注下期还款日
4. **与¥25K/月的关系** — 老婆信用卡的还款包含在每月¥25K中，不属于波总额外现金流出
5. **利率** — 信用卡分期利率一般不显示在截图中，留空

⚠️ 老婆信用卡总量不算大（~¥16K），但每月 ¥25K 转过去后具体怎么分配是黑盒——系统只知「转出¥25K」，不知其中多少用于还卡、多少用于养家、多少她自己消费。

### CLI

```bash
# 记录其他收入（妈妈转回、报销到账等）
income.py log -y 2026 -m 6 -o 14002 -n "妈妈转回"
```

### 批量导入银行流水收入（首次补全历史数据）

当从银行 PDF 提取到 12+ 个月的收入数据时，不要逐条跑 `income.py log`（太慢且它只支持单月单次）。直接操作 `income.json`：

1. 读取银行分析报告中的月度汇总
2. 为每个有数据的月份创建一条 `records` 条目
3. 保留已有记录（不覆盖），追加新发现的历史月份
4. 每条 notes 标注「（银行流水提取）」作为来源
5. 不要动 `monthly_baseline` 字段（那是波总口述的粗估，与银行实际数互不替代）

```python
# 批量导入模板
income['records'].append({
    "period": "2026-01",
    "salary": 52794.46,           # 银行工资代发总额
    "bonus_prorated": 10400,      # 保留波总口述的年度奖金均摊
    "bonus_extra": 36210.0,       # 额外奖金（银行提取）
    "other_income": 10000.0,      # 他行汇入等
    "total": 62794.46,
    "notes": "工资¥52,794（含补充代发）+ 备用金¥10,000（银行流水提取）",
    "logged_at": "2026-07-02"
})
```

⚠️ 银行数据和波总口述的收入口径不同——银行只捕捉到卡到账的，妈妈的微信转回、现金等不在银行流水里。两者可以并存，在 notes 里标明来源即可。

### 净现金流计算

```bash
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
| 📎 CSV/xlsx | 波总发导出文件（支付宝CSV是GBK，微信是xlsx） | import_csv.py 自动解析 + 编码检测 + 格式检测 |

- **支付宝** → `.zip` 内含 GBK CSV → `import_csv.py` 自动解压 → 解码 → 跳过元数据 → 解析
- **微信** → `.xlsx` → `import_csv.py` 通过 `openpyxl` 直接读取（`parse_wechat_xlsx()` 函数）

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

## 银行对账单处理管线（银行PDF → 结构化数据）

当波总发来手机银行短信（含解压密码）并确认邮件已发送到 Gmail 时，按以下流程处理。

### 步骤1：搜索银行邮件

方式A（Himalaya — 快速浏览）：
```bash
himalaya envelope list -a gmail --page-size 200 | grep -i "银行\|abc\|95555\|95588\|icbc"
```

方式B（Python imaplib — 下载附件）：
```python
import imaplib, email
with open('/Users/mac/.config/himalaya/gmail-app-password') as f:
    pwd = f.read().strip()
imap = imaplib.IMAP4_SSL('imap.gmail.com', 993)
imap.login('wangbo8805@gmail.com', pwd)
imap.select('INBOX')
# 按发件人搜索（ASCII safe）
result, data = imap.search(None, '(FROM "abc-mobile-bank@abchina.com" SINCE "01-Jul-2026")')
# 或遍历全部后 20-50 封：imap.search(None, 'ALL') → all_ids[-30:]
```

### 步骤2：下载附件

用 `imap.fetch(mid, '(RFC822)')` 拉取完整 MIME 消息，遍历 `msg.walk()` 找 `part.get_filename()` 非空的 attachment。Himalaya v1.2.0 无 `save-attachment` 命令，必须用 Python imaplib。

⚠️ **IMAP 状态陷阱**：`search()` 前必须先 `imap.select('INBOX')`，否则报 `SEARCH illegal in state AUTH`。

### 步骤3：解压加密 ZIP

常见银行 ZIP 压缩方式差异：

| 银行 | 加密方式 | 解压工具 | 密码来源 |
|------|---------|---------|---------|
| 农业银行 | AES-256（compress_type=99） | `7z` (p7zip) | 短信 | 
| 招商银行 | 标准ZIP加密 | `7z` 或 Python `zipfile` | 招行App→流水打印→申请记录 |
| 工商银行 | 不加密（直接PDF） | 无需解压 | 无 |

**铁律**：Python 内置 `zipfile` 不支持 AES-256 解压（`That compression method is not supported`）。必须用 `p7zip`：
```bash
brew install p7zip  # 首次安装
7z x <file.zip> -p<password> -o<outdir>/ -y
```

⚠️ **每家银行密码独立** — 波总短信发的是农业银行的密码。招商银行需要在招行App里单独查，工商银行通常不加密。必须逐个确认，不要假设所有 ZIP 用同一个密码。

### 步骤4：解析银行 PDF

中国三大银行 PDF 格式差异大，按各自格式解析：

**农业银行（ABC）** — 13页起
- 账户: 6228484101670076415
- 格式: `交易日期 交易时间 交易摘要 交易金额(±) 本次余额 对手信息 日志号 交易渠道 交易附言`
- 摘要: `转存(+)/微信支付(-)/财付通(-)/支付宝(-)/跨行汇款/他行汇入`
- 附言含详细商户名（如 `NA2026010905155216519793710210402相思椒餐饮...`）

**招商银行（CMB）** — 16页起
- 账户: 6214********5398（长沙麓谷支行）
- 格式: `记账日期 货币 交易金额(±) 联机余额 交易摘要 对手信息`
- 摘要: `快捷支付/转账汇款/代发款项/银证转账`
- 注意表格跨页时重复表头，需跳过

**工商银行（ICBC）** — 6页起
- 账户: 6212262317000300695
- 格式: `交易日期 时间 储种 摘要 地区 收入/支出金额 余额 对方户名 对方账号 渠道`
- 摘要: `微信零钱提现(+)/消费(-)/跨行汇款/他行汇入/贷款本息`
- 注意金额分「收入金额」和「支出金额」两列（不是带符号的单列）

### 步骤5：去重分析（关键）

银行 PDF 中大量交易是**支付宝/微信过路消费**（已在 `expenses.json` 中），直接导入会产生大量重复。

**去重策略**：
1. **支付宝/微信过路**（摘要含"支付宝""财付通""微信支付"）→ 大概率已在 expenses.json → 标记 probable_existing，不导入
2. **精确去重**：按 `日期_金额_商户名前6位_来源` 匹配 expenses.json 的 `dedup_key` 字段
3. **银行独有交易**（跨行汇款/贷款本息/银证转账）→ 这些不会在 expenses.json 中，按需导入
4. **自转跳过**（王波账户间转账）→ 不是消费也不是收入，直接跳过

典型结果（以千条数据规模）：
- ~55% 支付宝/微信过路 → 已有
- ~30% 新增（银行级交易）
- ~5% 收入 → 入 income.json
- ~1-2% 债务还款 → 核对 debts.json
- ~5% 自转跳过

### 步骤6：使用产出

**A) 收入数据 → income.json**

银行 PDF 是填充收入数据的**最佳来源**（工资代发、奖金、他行汇入）。提取所有正金额交易 + 工资代发，按月份汇总后批量导入 income.json。

```python
# 为每个有数据的月份创建一条记录
income['records'].append({
    "period": "2026-01",
    "salary": 52794.46,
    "bonus_prorated": 10400,
    "bonus_extra": 0,
    "other_income": 10000.0,
    "total": 62794.46,
    "notes": "工资¥52,794（含补充代发）+ 备用金¥10,000（银行流水提取）",
    "logged_at": "2026-07-02"
})
```

⚠️ 银行流水是**首次填充收入数据的唯一途径**（波总不记收入，只口述粗估）。导入后收益：获得 12+ 个月的完整收入画像。

**B) 债务发现 → 核对 debts.json**

银行还款记录中可能发现未追踪的债务（如携程金融、各类贷款等）。将还款对手方与 `debts.json` 的 `creditor` 字段逐一比对，有未追踪的向波总确认：

| 发现场景 | 处理 |
|---------|------|
| 还款记录在 debts.json 中有对应债务 | 正常，可忽略或记录为历史还款 |
| 还款记录但 debts.json 中无此债主 | 向波总确认：还有余额吗？要录入吗？ |
| 已清债务的尾款 | 确认 debts.json 的 cleared 中已有 |

**C) 新增消费 → 酌情导入**

银行独有的消费（非支付宝/微信过路）可酌情导入 expenses.json：跨行汇款（Dily转账等）、保险扣款、贷款利息。大多已在 Alipay/WeChat CSV 中覆盖，不需要导入。

## 邮件拉取（Gmail + Himalaya）

Himalaya CLI v1.2.0 (Homebrew) 不支持 oauth2/keyring。配置 Gmail 用 App Password + IMAP：
1. 打开 https://myaccount.google.com/apppasswords 生成 16 位密码
2. 在 Mac 终端跑 `himalaya` 交互式向导 → 选 gmail → 输 App Password
3. 如果向导不工作（TTY 限制），用 Python IMAP 直连（见 `references/gmail-app-password-setup.md`）
4. 拉取支付宝账单邮件（发件人 service@alipay.com）→ 解压 CSV → import_csv.py 导入
详细配置陷阱见 `references/gmail-app-password-setup.md`
附件下载陷阱见 `references/gmail-attachment-download.md`

## 🧠 波总沟通偏好（财务专属）

本会话发现的工作流偏好，嵌入到财务技能而不是 memory，确保下次会话自动遵循：

| 场景 | 偏好 | 原因 |
|------|------|------|
| 波总问"我的负债/总负债" | 先问"哪些有变动？"再输出 | 数据可能过时，直接输出容易出错。先收集更新再出全景 |
| 波总说"XX抵掉了/用其他方式"（非现金还款） | 标记为 amount=0 + notes="其他方式抵账"，移入 cleared。不记录为还款交易 | 不是现金流入/流出，不应出现在还款流水里 |
| 花呗截图 | 截图中的"7月账单累计 ¥X" = **总待还余额**（不是新增消费）。账单周期（如 6/5~7/4）是消费归属期 | 波总明确确认单数即总账，不要追问"是新增还是总欠款" |
| 拿去花截图 | "全部待还 ¥X" = 总余额；"X月X日待还 ¥Y" = 未出账部分。拿去花有"未出账"概念，总待还 > 未出账金额 | 直接更新 amount 为"全部待还"值 |
| 新增自债（非现金动用） | 创建 ID=I001/2/3（I 系列独立编号）, type="其他", rate=0, notes 标注时间预期 | 如基金储备款被消费占用，1-2个月内填回 |
| 短期承诺（1-2月填回） | 在 notes 标注 "X个月内填回" | 让波总明确还款时间窗口，系统自动追踪 |
| 还款日提取 | 截图中"还款日7月15日"即是到期日，更新到 `due_date` 字段 | 平台债 always 有固定还款日 |
| 债务置换建议 | 直接给推荐方案，不要列多选项让波总选 | 波总明确偏好——问"带多少出来"就按数据算一个数，而不是给A/B方案 |
| 收入修正 | 波总说"不对，实际是XX"时，立即停下用修正值重算所有结论 | 波总的数字比系统的数字更准（系统数据可能有口径误差） |

## 消费洞察生成流程（v2026-06-29）

当波总说"洞察我的消费"或"深度分析"时，按以下流程：

### 步骤1：数据清洗（先清洗再分析）

执行前务必先检查数据质量——**不清洗出洞察等于报假数**。

```python
# 快速审计
python3 -c "
import json
from collections import Counter
d = json.load(open('finance/expenses.json'))
# 检查非消费分类
bad = ['理财','分付还款','二维码收款','转账','红包']
for e in d['expenses']:
    if e['category'] in bad or (e['amount']>=2000 and '个人所得税' in e['merchant']):
        print(f'  🗑️ {e[\"date\"]} ¥{e[\"amount\"]:>8,.0f} [{e[\"category\"]}] {e[\"merchant\"][:30]}')
print(f'非消费 {len([e for e in d[\"expenses\"] if e[\"category\"] in bad])} 笔')
"
```

清洗清单：
1. **移除非消费** — 个人所得税/缴税、花呗还款、家庭大额转账（布尔乔亚≥¥2,000）、小荷包自动攒、余额宝定时转入
2. **合并重复分类** — `餐饮→餐饮美食`、`交通出行→交通`、`日用-快递→快递`、`交通-停车→停车`、`人情往来→人情`
3. **Recat「其他」类** — 按商户名判断归属，补充关键字到 `categories` 字段
4. **重新编号** — `e['id'] = f'E{i+1:03d}'`
5. **更新 meta** — total_amount/expenses/updated
6. cp 同步 + git push

### 步骤2：分析维度

| 维度 | 内容 | 输出信号 |
|------|------|---------|
| 📅 月度趋势 | 上月 vs 本月总额+日均 | 消费涨跌方向 |
| 💰 收入对比 | 月消费 vs 粗估收入¥40-50K | 留存空间 |
| 🏷️ 分类结构 | 餐饮/交通/日用等占比 | 消费画像（工作型 vs 享乐型） |
| 🔲 三层账户 | basic_living / relationship / event_reserve / business | 生活分账比例 |
| 🏪 商户集中度 | TOP10 占总额% | 供应商风险 / 可优化空间 |
| 🍜 餐饮深度 | 日均、高频商户、商务 vs 个人 | 外卖占比、商务招待频率 |
| 🚗 交通深度 | 高铁 vs 滴滴 vs 自驾 | 差旅模式 |
| ⚡ 异常峰值 | 单日超 3x 日均的日期 | 大额事件回溯 |
| 📆 周模式 | 周一~周日消费差异 | 周末 vs 工作日习惯 |

### 步骤3：输出结构

```
📊 波总消费深度洞察 | 截至 YYYY-MM-DD

总消费 ¥XX,XXX | XXX笔 | 笔均 ¥XX

📅 月度趋势: 5月¥X日均¥X → 6月¥X日均¥X | 6月预估¥X
💰 收入对比: 月收入¥40-50K | 消费占比XX% | 可留存¥X~¥X

🏷️ 消费结构（TOP6 + 其他汇总）
🏪 TOP10商户 + 集中度%
🍜 餐饮深度 + 交通深度
💼 经营独立分析（如可报销）
⚡ 峰值日TOP3

🎯 核心洞察（5-6条bullet，每条一句话）
   1️⃣ 结构判断
   2️⃣ 留存/风险管理
   3️⃣ 可优化点（滴滴高频/外卖占比）
   4️⃣ 可报销追踪提醒
   5️⃣ 还债空间
```

### 步骤4：AI 交接 JSON

当波总说"打成JSON"但上下文在讨论消费洞察 → 生成 `reports/consumption_deep_analysis.json`（类型一）。格式见 `references/consumption-analysis-schema.md`。

### ⚠️ 常见陷阱

- **不清洗就分析**：税/花呗/转账蹭在消费里，"其他"类占 50%+，洞察全是错的
- **分类合并遗漏**：`餐饮`和`餐饮美食`是两个独立分类但意思一样，必须合并后再出占比
- **布尔乔亚处理不当**：日常小额→餐饮美食/layer=relationship/sub=personal；大额≥¥2,000→从 expenses 移除（家庭转账）
- **小荷包残留**：每天¥0.33 看起来不起眼，但连续30天×¥0.33=¥10，虽然金额小但污染"笔数"统计

## 债务置换分析（低息贷款替换高息债）

当波总获得低息信贷额度（如工行 3%）时，按以下流程计算最优置换方案：

### 流程

1. **读现行债务** — 从 debts.json 提取所有 active 债务的金额和利率
2. **确定新贷利率** — 如工行 3%（年化单利）
3. **逐笔比对**：
   - 利率 > 新贷利率 → 置换有正收益
   - 利率 < 新贷利率（或无息）→ 不置换（换了反而多付利息）
   - 亲友无息债 → 不置换（换了从 0% 变 3%，每年倒贴钱）
4. **计算年省利息**：`年省 = 金额 × (原利率 - 新利率)`
5. **额度检查**：置换总额 ≤ 可用授信额度

### 利率估算

| 债种 | 估算利率 | 备注 |
|------|---------|------|
| 花呗 | ~15% | 消费信贷产品，实际可能更高 |
| 拿去花 | ~18% | 携程系消费贷 |
| 度小满 | ~12% | 百度系贷款 |
| 妈妈/二爸 | 4.7% | 已知明示利率 |
| 亲友无息 | 0% | 未标注利率的亲友债视为0 |
| 工行贷款 | 3% | 最便宜的资金来源 |

### 输出格式

```
推荐置换清单（利率 > 新贷利率）:
  ✅ 花呗     ¥13,730  (15% → 3%)  年省¥1,648
  ✅ 拿去花    ¥10,481  (18% → 3%)  年省¥1,572

  置换合计: ¥40,488
  年省利息: ¥4,685
  额度: 充足/不足
```

⚠️ **波总偏好**：算一个最优方案直接说，不要列 ABC 方案让他选。要借多少、还哪些，一锤子。如果他不认同，他会自己说。

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
11. **支付宝 CSV 编码 + 前导元数据行** — 支付宝导出的 ZIP 内 CSV 是 **GBK** 编码，且前 1-22 行是元数据（导出信息、统计摘要等），不含 CSV 表头。`import_csv.py` 现已内置自动处理：`_read_csv_with_encoding()` 按 utf-8-sig → gbk → gb2312 → latin-1 顺序尝试解码；`_find_csv_header()` 扫描包含 `[交易时间,交易分类,交易对方,商品说明]` 的行作为真实表头，跳过前导元数据。**无需手动 iconv 转换**，直接 `python3 import_csv.py <gbk_csv>` 即可。
12. **CSV 日期范围** — 微信账单导出时注意终止时间要选当前日期，否则会漏掉最近几天的数据
13. **截图 vs CSV 优先级** — 同一笔交易 CSV 的商户名更准确（截图 OCR 可能误读"明红蹄花"的供应商名），优先保留 CSV 版本
14. **分类关键字自动学习** — 每次发现新的商户名模式（如"蹄花""龙森园""相思椒"），立即追加到 `expenses.json` 的 categories 关键字库。⚠️ **batch 导入后必须检查**：`grep '"其他"' expenses.json` 找出被归入"其他"的项 → recat 纠正 → 把商户关键字补入 `expenses.json` 的 categories 字段。已知常被误归"其他"的商户：DeepSeek API→经营-软件服务、阿里云→经营-软件服务、顺丰→日用-快递、享道出行→交通、安徽蒸小碗/XX蹄花/XX小碗→餐饮、直豆→娱乐、湖南计算智谷/XX物业→交通-停车、App Store/Apple Music→数码
15. **JSON输出类型混淆** — 波总说"打成JSON"时若上下文中提到"消费流水""深度分析""洞察"，必须出 `consumption_deep_analysis.json`（类型一），不要出 `bog_finance_portrait_handoff.json`（类型二）。类型一是深度洞察，类型二是全景快照。判断标准：看波总是否在讨论消费数据。
16. **Layer 默认值** — 新录入的消费默认 layer 为 `basic_living`。商务招待/经营相关必须在录入时手动指定 `--layer business`，或事后 `expenses.py recat` 纠正。
17. **外部AI金额建议不盲从** — 外部报告提出的具体金额阈值（如"月¥18-20K"）是主观估算，不是实测数据。必须先跑满3个月 layer 分布再定阈值，不要直接写入系统配置。
18. **⚠️ Cron 脚本路径陷阱（no_agent 模式）** — `no_agent=true` 的 cron job 使用相对路径 `script` 时，解析到 profile 的 `scripts/` 目录（如 `~/.hermes/profiles/finance/scripts/`），不是 adjutant 的 `finance/scripts/`。必须把脚本复制到 profile scripts 目录才能被 cron 找到：`cp ~/.hermes/adjutant/finance/scripts/nag_screenshots.py ~/.hermes/profiles/finance/scripts/`。这和 pitfall #10 的 `expanduser` 陷阱是不同的路径解析问题。
19. **平台债类型发现** — 系统当前追踪 4 种平台债（花呗/拿去花/度小满/工行贷款），但截图可能暴露未追踪的新平台债（如微信分付、借呗、微粒贷等）。遇到截图或**银行记录中的还款记录**但 creditor 不在 debts.json 中时，必须主动询问波总总余额和还款日，不要默默忽略。银行还款记录中发现携程金融等未追踪债是常见场景。
20. **分付特殊处理** — 微信分付是 ¥4,000 额度、18-20% 利率的临时周转工具。波总用完即填（6/6 还款 ¥479.22 已清零）。**不加入 debts.json**（非固定债），但作为高风险工具备忘。铁律：绝不让分付滚到下个账单周期。其他类似 revolving credit 同理。
21. **截图 OCR 管线（v4.0，2026-06-12 波总指定优先级）** — 引擎优先级：🥇千问 VL API (dashscope/qwen-vl-max) → 🥈 Apple Vision (Swift) → 🥉 Tesseract (`chi_sim`)。详见 `debt-screenshot-auto-update` 技能的 "OCR 引擎" 章节。
22. **数据文件双重同步（🛑 血坑 — 2026-06-25 再次翻车）** — `~/.hermes/adjutant/finance/`（工作副本）和 `~/.hermes/adjutant/repo/hermes-adjutant/finance/`（Git 仓库）是两个独立目录。**铁律：所有 patch/write 操作直接指向 repo 路径**，不要碰工作副本。`finance.py`/`expenses.py` 写入前者，git 仓库是后者。如果不小心改了工作副本，必须立即 cp + git push。commit 前用 `diff` 检查两副本一致。<br>
    - **脚本模式**：`finance.py repay / expenses.py add` → 自动写入工作副本 → `cp` 到 repo → git push<br>
    - **直接编辑模式（🛑 危险）**：必须写 repo 路径，不得碰工作副本
23. **⚠️ Git pull 快照冲突（多 AI 并行）** — 本地 `snapshots/YYYY-MM-DD.json` 为 untracked 文件，远程已有同名文件时 `git pull` 报错：`error: untracked working tree files would be overwritten by merge`。解法：`rm -f finance/snapshots/YYYY-MM-DD.json && git pull origin main`。根本原因是周报 cron 创建的本地 snapshot 未 add+commit 就被其他 agent push 的同名文件阻塞。
24. **⚠️ Cron `cd` 路径解析** — Cron 会话中 `cd ~/.hermes/...` 的 `~` 被 profile 覆盖，解析到 profile sandbox（如 `/Users/mac/.hermes/profiles/finance/home/.hermes/...`）。所有 `cd` 和相对路径必须改用绝对 `/Users/mac/...`。关联 pitfall #10（态B）。
25. **⚠️ Batch 去重误杀：同日同金额段交易** — `expenses.py batch` 去重逻辑为 `日期相同 + 金额差≤¥2 + 商户名相似度>0.5`。同品类同日相近金额会被误判。**真实案例**：6/8 滴滴快车-宋师傅 ¥18.90 被误判为 滴滴专车-袁师傅 ¥19.00 的重复（similarity 0.75），实际是两笔独立行程。**解法**：确认非真重复后，用 `python3 -c` 手动追加到 expenses.json 再 cp+push。常见误杀场景：滴滴×N、美团外卖×N、同一商户多笔近距离消费。手动插入模板：
    ```bash
    python3 -c \"
    import json; p='/Users/mac/.hermes/adjutant/finance/expenses.json'
    with open(p) as f: d=json.load(f)
    d['expenses'].append({'id':f'E{len(d[\\\"expenses\\\"])+1:03d}','date':'...','amount':...,'merchant':'...','category':'...','layer':'basic_living','source':'支付宝','dedup_key':'...','created_at':'...','reimbursable':True})
    d['meta']['total_expenses']=len(d['expenses']); d['meta']['total_amount']=round(sum(e['amount'] for e in d['expenses']),2)
    with open(p,'w') as f: json.dump(d,f,ensure_ascii=False,indent=2)
    \"
    ```
26. **⚠️ import_csv 过滤掉了保险 — 需要保险数据时直接 grep CSV** — `import_csv.py` 的过滤规则明确跳过「保险」类别（归入理财/保险过滤）。当波总需要分析保险支出时，直接在原始 CSV 中 `grep -i \"保险\"` 提取，不要走 import_csv。提取流程见 `references/insurance-policy-analysis.md`。
27. **支付宝 ZIP 解压编码问题** — 支付宝导出的 ZIP 文件名含中文，Windows 端创建导致编码不兼容。`unzip -P <密码>` 可能报 `Illegal byte sequence`。优先用 Python `zipfile` 模块：`zf.setpassword(b'密码')` + `zf.extract()` 可绕开中文文件名编码问题。
28. **⚠️ import_csv.py 现在同时支持支付宝 CSV 和微信 xlsx** — 不再需要分别调用不同脚本。直接 `python3 import_csv.py <文件>` 即可，脚本自动根据扩展名和文件内容检测格式。支付宝 CSV 通过 `_read_csv_with_encoding()` 自动尝试 utf-8-sig → gbk → gb2312 → latin-1；通过 `_find_csv_header()` 扫描包含 `[交易时间,交易分类,交易对方,商品说明]` 的行作为真实表头，跳过前导元数据。微信 xlsx 通过 `parse_wechat_xlsx()` 函数读取，从第一行扫描到包含 `[交易时间,交易类型,交易对方,商品]` 的表头行，跳过前导元数据。
29. **⚠️ 微信 xlsx 过滤规则** — `parse_wechat_xlsx()` 只保留 `交易类型=商户消费` 或 `扫二维码付款` 的支出项。`转账`、`红包`、`零钱提现`、`转入零钱通` 等一律跳过。这意味着微信账单中的大量转账（如车位费转账、妈妈转回）不会被计入消费——如果波总需要这些转账数据做关系流向分析，需另行提取。
30. **⚠️ 导入后必须手动检查重复记录** — `import_csv.py` 的去重键是 `日期_金额_商户名前6位_来源`，但同一笔交易在不同来源（截图OCR vs CSV vs 支付宝原始）可能有不同商户名，导致重复。支付宝CSV导入后常见重复：龙森园餐饮、携程旅行网、滴滴出行。微信 xlsx 导入后常见重复：火车票。导入后用 `python3 -c` grep 大额重复金额项，手动删除冗余记录，更新 meta。
31. **⚠️ QQ邮箱不支持标准 OAuth2 IMAP** — QQ邮箱无法通过 Himalaya CLI 的 OAuth2 流程授权。必须使用 **16位授权码**（在 QQ邮箱设置 → 账户 → IMAP/SMTP服务 中开启后获得）。如果波总找不到授权码入口，退而求其次：每次导出账单后直接把 zip/xlsx 文件发给我，我自动解压解析。
32. **⚠️ 支付宝账单解压密码每次随机** — 不是身份证后6位，每次导出都生成一个随机密码。密码在支付宝消息对话框中显示（不是邮件里）。所以邮箱自动拉取流程是：波总在支付宝导出账单 → 发到指定邮箱 → 把解压密码发给我 → 我去邮箱拉附件 → 解压 → 导入。如果邮箱扫描不可用，波总直接把 zip 文件发给我即可。
33. **月度消费分析报告必须有洞察+预测+趋势对比** — 波总明确要求：不只是记录流水，要有趋势预测（按当前消费速度推算年底总额）、同期对比（vs 上月/vs 去年同期）、结构洞察（哪些类别占比高、哪些可优化）、优化建议（基于数据的理性建议，不拍脑袋）。报告结构：核心洞察 → 趋势预测 → 同期对比 → 结构分析 → 优化建议 → 异常预警。
34. **⚠️ App Password 方式（非 OAuth2）连 Gmail/邮箱** — QQ邮箱/部分邮箱不支持标准 OAuth2 IMAP。Himalaya 连 Gmail 的可靠方式是：Google Account → 开启两步验证 → https://myaccount.google.com/apppasswords → 创建 App Password → 存 macOS Keychain → himalaya config.toml 用 `backend.auth.cmd` 从 Keychain 读取。详见 `references/gmail-app-password-setup.md`。
36. **⚠️ 手机远程指挥 Mac 的标准模式** — 波总常用手机不在 Mac 旁时的操作模式：手机发指令 → 需要 Mac 本地操作的步骤（浏览器登录、输入验证码/App Password）由波总手机完成 → 把结果（授权码、截图、确认截图）发给我 → 我后台执行配置/验证。关键：把"人肉操作"和"后台自动化"拆解清楚，不要让波总在 Mac 终端操作。

37. **⚠️ Himalaya v1.2.0 auth.cmd 路径陷阱（2026-06-17 确认）** — Himalaya 用 `backend.auth.cmd` 从外部命令获取密码。profile sandbox 中 `~` 被改写成 `/Users/mac/.hermes/profiles/finance/home`，所以 `auth.cmd` 里的 `~/.config/himalaya/gmail-app-password` 会解析到错误路径。**解法：auth.cmd 必须用绝对路径**，如 `cat /Users/mac/.config/himalaya/gmail-app-password`。App Password 文件放在 `/Users/mac/.config/himalaya/gmail-app-password`（600 权限），不要用 Keychain（sandbox 环境下 `security` CLI 报 exit 44，Keychain 条目不可访问）。Himalaya 配置正确路径后可直接 `himalaya envelope list --page-size 100` 拉邮件。
38. **⚠️ Himalaya v1.2.0 没有 `save-attachment` 命令** — `message save` 是存邮件到文件夹，`message export` 导出原始邮件到临时目录但不直接提取附件。下载邮件附件的可靠路径是用 Python `imaplib` 直连 IMAP，`imap.fetch(msg_id, '(RFC822)')` 拿到完整 MIME 消息后解析 multipart 找 attachment 部分。详见 `references/gmail-attachment-download.md`。
39. **⚠️ Himalaya 搜索中文主题需要 ASCII-safe 搜索条件** — `himalaya envelope list` 的搜索语法不支持中文关键词（会报 parse error）。搜索 Gmail 时建议用 ASCII 条件：`FROM service@mail.alipay.com` 或 `SUBJECT 交易`（英文关键词），不要在命令行传中文。Himalaya 的 IMAP 搜索底层也受 ASCII 限制。
41. **⚠️ Gmail 拉取支付宝账单完整管线** — 详见 `references/gmail-alipay-billing-pipeline.md`。支付宝每月导出账单时会自动发邮件到指定邮箱（发件人 `service@mail.alipay.com`），附件为 ZIP（密码随机）。完整流程：
    1. `himalaya envelope list -a gmail --page-size 200` 拉最近邮件
    2. `himalaya message read <envelope_id>` 确认有附件
    3. 用 Python `imaplib` 直连下载附件（Himalaya v1.2.0 无 `save-attachment` 命令）
    4. `zipfile.setpassword(b'<密码>')` 解压 ZIP → CSV
    5. 用 `import_csv.py` 或专用 GBK 解析器导入
    6. 同步 + git push
47. **⚠️ recalc_debt_meta() 不会自动适配新 debt type（🛑 2026-06-27 翻车复盘）** — `finance.py` 的 `recalc_debt_meta()` 硬编码只累加 `type == "亲友"` 和 `type == "平台"`。当新增 `type == "其他"`（如 I001 基金储备自债）时，`grand_total` 漏算了这笔。**症状**：日报数据与波总的石墨 Excel 对不上，差了一个 type 的全部金额。<br>
    - **修复模式**：每次在 debts.json active 中新增一个 `type` 值，必须同步修改 `recalc_debt_meta()` 的求和逻辑<br>
    - **正确的代码模式**：`other_active = sum(... for d in debts["active"] if d["type"] == "其他")` + `grand_total = family + platform + other`<br>
    - **事后验证**：运行 `python3 -c "import json; d=json.load(open('finance/debts.json')); actual=sum(x['amount'] for x in d['active']); print(f'meta={d[\"meta\"][\"grand_total\"]}, actual={actual}, diff={d[\"meta\"][\"grand_total\"]-actual}')"` 检查对齐

48. **⚠️ baseline 与 grand_total 的浮点精度差** — `config.json` 的 `baseline_grand_total` 设为整数（如 `530138`），但 `debts.json` 的 `grand_total` 是浮点计算结果（如 `530137.88`）。差 ¥0.12 会导致日报进度显示 `-1.7%`。**解法**：设 baseline 时从 `grand_total` 取值，不要手写整数。`cp` 同步后必须 `diff` 验证所有 .json 文件。

42. **⚠️ 布尔乔亚(余玓瓅) = 老婆消费分类规则** — 商户名"布尔乔亚(余玓瓅)"对应老婆余玓瓅的消费。分类要点：
    - 日常小额消费（¥15-¥123）→ 归入 **餐饮美食**，layer=relationship, sub_category=personal
    - 大额转账（如 ¥5,000）→ **不是消费**，应从 expenses.json 中移除（这是家庭转账，不是支出）
    - 同日同金额出现 2 次的扣款（如 ¥224×2, ¥275.9×2）→ 多为自动续费/订阅代扣，需进一步确认性质
    - 6/13 出现 10 笔小额重复扣款（¥15-¥47）→ 疑似批量自动续费，建议查支付宝"免密支付/自动扣款"列表

43. **⚠️ 支付宝账单邮件完整处理管线（2026-06-18 确认）** — 当波总发来支付宝账单邮件通知（含"处理中"状态）时：
    1. 邮件本身只有通知文字，**实际CSV在加密ZIP附件里**
    2. **用 imaplib 搜索时消息 ID 与 Himalaya 显示的不同** — Himalaya 的 envelope ID（如 13038）是 Gmail 的 UID，而 imaplib `fetch()` 用序列号。正确做法：用 `imap.search(None, 'FROM "service@mail.alipay.com"')` 获取真实 ID 再 fetch。
    2. 附件文件名含中文（如`支付宝交易明细(20260616-20260618).zip`），用Python `imaplib` 直连下载（Himalaya v1.2.0无`save-attachment`命令）
    3. ZIP是**加密的**，密码每次随机，在支付宝App"我的-账单-开具交易流水证明-申请记录"中查看，或通过支付宝服务消息获取
    4. 用Python `zipfile` + `zf.read(name, pwd=b'密码')` 解压（不用系统unzip，中文文件名会报`Illegal byte sequence`）
    5. CSV是**GBK编码**，用`data.decode('gbk', errors='replace')`解析
    6. CSV前22行是元数据（导出信息、统计摘要等），从第24行header开始才是数据
    7. 数据列：`交易时间,交易分类,交易对方,对方账号,商品说明,收/支,金额,收/付款方式,交易状态,交易订单号,商家订单号,备注`
    8. **只提取`收/支`列为"支出"或"还款"的行**，"不计收支"的行跳过
    9. 支付宝小荷包自动攒（如¥0.33）属于内部转账，不计消费
    10. 去重：与现有expenses.json按`日期_金额_商户名_支付宝`键比对，已有则跳过
    11. 新增记录后更新meta.last_updated，cp到repo，git commit+push
    12. 完整验证管线见 `references/gmail-alipay-pipeline-verified.md`（2026-06-29 实测，含翻车记录）
44. **⚠️ Gmail IMAP 拉取支付宝账单 — 两类密码严格区分（2026-06-21 新增）** — 两个完全不同的密码：
    - **Gmail App Password**（16位字母数字）：用于 IMAP 登录 Gmail 拉邮件。存放在 `/Users/mac/.config/himalaya/gmail-app-password`。用普通密码会报 `AUTHENTICATIONFAILED`。
    - **支付宝 ZIP 解压密码**（6位数字，每次随机）：用于解压邮件附件中的 ZIP。由波总在支付宝App中获取后发给我。
    下次拉账单时，先确认波总发的是哪个密码。
45. **⚠️ Python imaplib 搜索限制（2026-06-21 新增）** — 三个铁律：
    - 搜索条件只能用 ASCII，中文 Subject 会 `UnicodeEncodeError`
    - 必须先用 `FROM "service@mail.alipay.com"` 缩小范围，否则搜全部邮件 300s 超时
    - Himalaya `envelope list` 只返回最近10封，无分页，历史邮件必须用 imaplib
46. **⚠️ IMAP 搜索中文主题失败时的兜底方案（2026-06-23 新增）** — 当 `himalaya envelope list 'subject 支付宝'` 或 `imap.search(None, 'SUBJECT "支付宝"')` 因编码问题失败时：
    1. 先用 `imap.search(None, 'ALL')` 获取全部邮件ID
    2. 遍历最近 N 封（如 `all_ids[-20:]`），对每封 `fetch(mid, '(BODY.PEEK[HEADER])')` 拿原始 header
    3. 从 raw header 字符串中 `if '支付宝' in line` 或 `if 'alipay' in line.lower()` 过滤
    4. 找到目标邮件后，再用 `fetch(mid, '(RFC822)')` 拉完整 MIME 消息
    5. 解析 attachment 部分，提取 ZIP 附件
    注意：`imap.select('INBOX')` 必须在 `search` 之前调用，否则会报 `SEARCH illegal in state AUTH`

49. **⚠️ import_csv 仍有非消费条目漏网（2026-06-27 审计发现）** — `import_csv.py` 过滤了理财/转账/红包/还款等，但旧数据或手动录入时仍有漏网。**症状**：expenses.json 中混入分类为「理财」「分付还款」「二维码收款」「红包」「转账」的条目，污染总金额（真实案例：305 笔 ¥38,110 理财流水混在消费数据中）。**审计与清理**：
    ```bash
    cd ~/.hermes/adjutant/repo/hermes-adjutant
    python3 -c "
    import json
    with open('finance/expenses.json') as f: ex=json.load(f)
    bad=['理财','分付还款','二维码收款','红包','转账','转账-妈妈','转账-李杰','转账-nevis']
    bad_items=[e for e in ex['expenses'] if e['category'] in bad]
    print(f'{len(bad_items)} 笔, ¥{sum(e[\"amount\"] for e in bad_items):,.2f}')
    ex['expenses']=[e for e in ex['expenses'] if e['category'] not in bad]
    ex['meta']['total_expenses']=len(ex['expenses'])
    ex['meta']['total_amount']=round(sum(e['amount'] for e in ex['expenses']),2)
    ex['meta']['updated']='2026-06-27'
    with open('finance/expenses.json','w') as f: json.dump(ex,f,ensure_ascii=False,indent=2)
    print('✅ 已清理')
    "
    ```
    清理后必须 cp 同步 + git push。

50. **⚠️ 老婆 Dily 信用卡不在 debts.json 中** — Dily 的信用卡债务（中信/建行）**未录入 debts.json**，仅在我记忆或石墨 Excel 中有记录。系统日报/周报不会自动追踪信用卡的还款日和余额。**每当波总问"Dily 信用卡情况"时**：
    - 先查记忆和 session 中的历史记录
    - 主动问波总有没有新截图或新账单
    - 如果波总想加进 debts.json，建议创建 `type="信用卡"` 条目并同步更新 `recalc_debt_meta()`
    - 6/18 历史：中信 ¥3,712.71（7月6日到期），建行 ¥12,150.84（7月2日到期，后已还清）

52. **⚠️ 银行 ZIP 可能用 AES-256 加密 — Python zipfile 不支持（🛑 2026-07-02 翻车）** — 农业银行等使用 AES-256 加密（compression type=99），Python 内置 `zipfile` 报 `That compression method is not supported`。`unzip` 命令也无法解密 AES ZIP（只支持传统 PKWARE 加密）。**必须用 `7z`（p7zip）**：`brew install p7zip && 7z x file.zip -p<password> -o<outdir>/ -y`。验证：`7z l file.zip` 可正常列出内容但 Python `zipfile.ZipFile.infolist()` 的 `compress_type` 为 99。

53. **⚠️ imaplib search() 必须在 select() 之后** — 连接 Gmail 后 `imap.login()` → 必须先 `imap.select('INBOX')` 再 `imap.search()`。如果在 AUTH 状态直接 search，报 `command SEARCH illegal in state AUTH, only allowed in states SELECTED`。这是 IMAP 协议规定的状态机要求。

55. **⚠️ `finance.py repay` 输出说成功但文件没有更新（🛑 2026-07-02 发现）** — `finance.py repay -c "花呗" -a 10000` 输出 `"ok": true, "paid": 10000, "new_remaining": 3729.51` 但实际 debts.json 文件中花呗金额**没有变化**。症状：执行后立即检查文件，花呗余额还是原值。疑似脚本内 `write_json()` 未正确执行或路径写到了错误位置。<br>
    - **解法**：执行 `finance.py repay` 之后，**必须手动验证** debts.json 文件中的金额是否确实更新了。如果没更新，手动编辑 debts.json 修改对应条目的 `amount` 字段 + 更新 `meta` 的合计，然后用 `finance.py snapshot` 或者手动算一下 `grand_total`。<br>
    - **两步验证**：<br>
      ```bash
      # 先看 workdir
      python3 -c "import json; d=json.load(open('/Users/mac/.hermes/adjutant/finance/debts.json')); print([x for x in d['active'] if x['creditor']=='花呗'])"
      # 再看 repo
      python3 -c "import json; d=json.load(open('/Users/mac/.hermes/adjutant/repo/hermes-adjutant/finance/debts.json')); print([x for x in d['active'] if x['creditor']=='花呗'])"
      ```
**⚠️ 每家银行解压密码独立** — 农业银行短信中的密码只用于农行 ZIP。招商银行需要到招行App→流水打印→申请记录查自己的密码。工商银行直接发PDF不加密。不要用一个密码尝试解所有银行ZIP。
    - **解法**：执行 repay 后**必须手动验证** debts.json 中金额已更新。如未更新，直接编辑 debts.json 修改 `amount` + 重算 `meta.grand_total`。<br>
    - **验证命令**：`python3 -c "import json; d=json.load(open('/Users/mac/.hermes/adjutant/finance/debts.json')); print([x['amount'] for x in d['active'] if '花呗' in x['creditor']])"`

**⚠️ 每家银行 ZIP 密码独立——不要假设同一密码通吃** — 波总短信发的密码（如 800562）是农业银行的。招商银行需要到招行App→流水打印→申请记录 查另一组密码。工商银行通常直接发 PDF 不加密。在等待用户的确认前，不要尝试用错误的密码硬解。

51. **⚠️ 支付宝 CSV 三关过滤（🛑 2026-06-29 修复）** — `import_csv.py` 的 `parse_alipay_row()` 原始只检查 `direction != "支出"`，但有致命缺口：**「不计收支」含"收""支"二字**，原有 `"收" in direction and "支" not in direction` 逻辑不命中 → 余额宝/小荷包流水混入消费。修复的三关过滤：

    **第1关 → 方向过滤（前置）**：
    ```python
    if "不计收支" in direction: return None
    if "收" in direction and "支" not in direction: return None
    if direction and "支" not in direction: return None
    ```
    **第2关 → `交易分类` 列过滤（新增）**：
    ```python
    tx_category = row.get("交易分类", "")
    skip_tx_cats = ["投资理财", "退款", "保险", "充值缴费-预存", "信用卡还款"]
    if tx_category and any(cat in tx_category for cat in skip_tx_cats): return None
    ```
    **第3关 → 关键字扩展**：新增 `小荷包`、`花呗分期还款`，`余额宝` 改为模糊匹配（原要求精确匹配"转入/转出"）。

    **验证**：支付宝 CSV 523行，旧逻辑 504笔（含222笔非消费），新逻辑 **125笔真实消费**。注意修复了 `parse_alipay_row` 中的 `parse_alipay()` 过时引用——当前代码是 DictReader 驱动的 `parse_alipay_row()`。
    - **余额自动转入/小荷包自动攒**：方向为"支出"，不被过滤（真实案例：每天¥500×30天=¥15,000 余额宝定时转入被当消费导入）
    - **支付宝小荷包**：自动攒¥0.33/次，方向"支出"，不是消费
    - **零金额条目**：部分交易为¥0.00（如亲我**寞），不应入库
    - **退款原始购买**：退款条目本身是"不计收支"（已过滤），但原始购买条目可能同时被导入（米莫**店¥203退款）
    - **地址**：`parse_alipay()` 新增了批量过滤逻辑：跳过 `tx_category="投资理财"`、`merchant/desc含小荷包`、`amount≤0`、`退款` in tx_category。核心铁律：**只要涉及支付宝内部资金流转（理财/余额宝/小荷包/定时转入），都跳过，不管方向字段**。
