---
name: finance-hub
description: 波总个人财务中枢 — 债务追踪、还款记录、里程碑游戏化、每周大盘推送。当你收到"还了XX YY元""花呗清了""我的债务"等财务相关指令时使用。
category: productivity
trigger: 还了|还款|债务|负债|花呗|借呗|还款进度|财务|欠款|清债
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
| `scripts/finance.py` | 核心引擎（repay / report / snapshot / milestones） |

## 交互模式：三种消息，不会搞混

| 波总说什么 | 你做什么 | 数据去向 |
|-----------|----------|----------|
| 「T051完成了」「新增任务XX」 | 副官任务管理 | `status.json` → Git push |
| **「还了花呗 2000」「妈妈还了 5000」** | **财务中枢还款** | `debts.json` → Git push |
| 「花呗清了」「XX还完了」 | 全额清空该债，移入 `cleared` | Git push |
| 「我的债务」「财务报告」 | 运行 `finance.py report` 输出大盘 | — |
| 「XX新增 ZZ 元」「借了 XX ZZ」 | 手动追加到 `debts.json` active 列表 | Git push |

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

## 自动推送

- **每周日晚 21:00**：Cron `1fa49ed0087e` 自动生成大盘 + Git push + Telegram 推送
- 报告内容：总负债 / 进度条 / 本周还款 / 同期对比 / 预测清债日 / 下个里程碑

## 陷阱

- **不要靠 memory/mem0 获取债务数据**——`debts.json` 是单一事实源
- **还款前先 git pull**——其他 AI 可能已更新
- **花呗等平台债金额会波动**——波总发截图时更新 `amount` + `updated_at` + `source`
- **投资款不是债权**——陈春兰投资款、王林投资款等不应出现在 debts.json 中
- **波总维护 Excel（石墨文档）作为原始记录**，系统追踪进度——双轨共存，不冲突
