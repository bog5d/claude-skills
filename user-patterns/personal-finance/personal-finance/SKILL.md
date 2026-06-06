---
name: personal-finance
title: "波总个人财务中枢 — 债务追踪 + 游戏化还款"
description: "管理波总的亲友债务和平台债务，记录还款，生成周报，游戏化激励。一句话交互：'还了XX N元'。"
category: user-patterns
trigger: "波总说还款、债务、财务、花呗、借呗、度小满、还钱、还了XX，或要求看债务进度/周报/财报"
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
├── snapshots/YYYY-MM-DD.json  ← 初始 + 周度快照
├── reports/                ← 周报生成区
└── scripts/finance.py      ← 核心引擎（repay / report / snapshot / milestones）
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

# 生成周报
python3 ~/.hermes/adjutant/finance/scripts/finance.py report

# 创建快照
python3 ~/.hermes/adjutant/finance/scripts/finance.py snapshot

# 查看里程碑
python3 ~/.hermes/adjutant/finance/scripts/finance.py milestones
```

## 自动化

| 机制 | 时间 | 内容 |
|------|------|------|
| Cron `1fa49ed0087e` | 每周日 21:00 | 生成快照 + 周报 + Git push + Telegram 推送 |
| 每次还款 | 即时 | 自动 git commit + push（不等 cron） |

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

## 陷阱

1. **不要手改 JSON，用 finance.py** — `finance.py repay` 已处理元数据更新、清债转移、交易记录，手改容易破坏一致性
2. **每次还款后必须 git push** — 和数据完整性相关，立即 `cd hermes-adjutant && git add -A && git commit && git push`
3. **债主名精确匹配** — 用 `-c "花呗"` 精确匹配 creditor 字段，不支持模糊。找不到时列出活跃债主名给用户
4. **不要把财务消息当副官任务** — "还了花呗2000"不是创建任务，是财务指令
5. **利率为空** — 大部分亲友债无利率，排序时 null 排最后
6. **已清债主重名** — 已清列表和活跃列表分开，匹配只查 active
7. **金额超额保护** — finance.py 自动 cap 到 0（不会变负），但超额的差额会提示
8. **Excel 双轨不同步** — 以波总口头确认为准，Excel 是历史参考。不用试图保持两边精确一致
9. **归途驿站禁止归并** — 生成报告/HTML 时，每笔亲友债必须独立一行，绝不合并"菊仙·陈建·刘小兵 ¥20K×3"这类归并行
