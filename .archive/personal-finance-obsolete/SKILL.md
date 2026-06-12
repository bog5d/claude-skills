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
├── transactions.json       ← 还款流水
├── snapshots/              ← 周度快照
└── scripts/
    ├── finance.py          ← 核心引擎（repay / report / snapshot / milestones）
    └── expenses.py         ← 消费追踪引擎
```

## 交互模型

### 记录还款
波总说一句话，自动识别债主和金额：
- "还了花呗2000" / "还了妈妈5000" / "拿去花清了"

### 查询债务
"我的债务" / "债务进度" / "还欠多少"

### 生成财报
"发一下最新财务报告" / "财报"

处理：读 debts.json → 计算分类合计 → 按高息优先排列 → 附带里程碑进度条。

## 报告格式

```
💰 波总财务中枢 — YYYY.MM.DD

总负债    ¥XXX,XXX
已清偿    ¥XXX,XXX+

🏠 亲友债务 — ¥XXX,XXX (N笔)
📱 平台债务 — ¥XX,XXX (N笔)

🎯 里程碑进度
🟩🟩🟩🟩⬜⬜⬜⬜⬜⬜  XX%

✅ 已清偿星火台
  🏆 老姚达州 ¥150,000
  ...
```

## 游戏化

### 里程碑
¥500K → ¥450K → ¥400K → ¥350K → ¥300K → ¥250K → ¥200K → ¥150K → ¥100K → ¥50K → ¥0

### 成就
🩸第一滴血 / 💀首杀 / 🔥五连杀 / ⚔️家族副本过半 / 📱平台清零 / ⛓️连续作战

## 核心命令

```bash
# 记录还款
python3 ~/.hermes/adjutant/finance/scripts/finance.py repay -c "花呗" -a 2000

# 生成报告
python3 ~/.hermes/adjutant/finance/scripts/finance.py report

# 快照
python3 ~/.hermes/adjutant/finance/scripts/finance.py snapshot
```

## 陷阱

1. 每次还款后必须 git push
2. 债主名精确匹配
3. 不要把财务消息当副官任务创建
4. 金额超额保护 — finance.py 自动 cap 到 0
5. Excel 双轨不同步 — 以波总口头确认为准