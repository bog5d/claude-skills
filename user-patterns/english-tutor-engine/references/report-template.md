# 学习报告生成模板

User approved format. Follow exactly.

## 30秒快照

```
段位：{rank}
今日局数：{X} 局
今日刷词：{Y} 词
正确率：{Z}%
连击：🔥{current}（历史最高：🔥{highest}）
总分：{pts}
估分：{score}
```

## 三组核心数字

**① 覆盖率 {coverage}%**
{reviewed}/{total} 个核心词交过手。剩余 {unseen} 个未碰。
决定广度——题来了认不认识。

**② 掌握率 {practiced_mastery}%**
交手过的 {reviewed} 词里，SM-2 推算平均牢固程度是 {practiced_mastery}%。
决定深度——认识但能立刻反应吗？

**③ 预测分 {score} 分**
纯词汇维度折算参考分。⚠️ 这只是词汇基础分。阅读/翻译/写作未激活（需覆盖率 ≥30%）。

## 历次 Session 走势

```
date ─── session ── words/score/accuracy
(手动从 progress.json.history 按天聚合)
```

## 交锋统计

```
胜 {correct} 次 ████████████ {accuracy}%
败 {mistakes} 次 ████████████

最高连击：🔥{highest_streak}
当前连击：🔥{current_streak}
```

## 错题族谱

{num_types} 种错误类型，{num_errors} 次有记录错误：

| 类型 | 次数 | 典型战例 |
|------|------|----------|
| ...  | ...  | ...      |

(从 sessions.json.error_log 提取)

**高频错词 TOP**：
- word — 错 X 次。症状：...

## 当前挂红标

mastery=0 且 review≥2 的词。无则写"无"。

## 已稳固的词（mastery ≥ 0.45）

```
word1 · word2 · word3 ...
```

下次它们自动排到更长间隔。

## 一句话总结

一段概括性描述。

---

## Output Instructions

1. Use Telegram markdown (**bold**, `code`, bullet lists)
2. Don't use tables in Telegram — use bullet lists or labeled key:value
3. Put summary at top, detail after
