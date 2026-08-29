---
name: name-ocr-verification
version: 1.0.0
author: hermes-curator
license: internal
metadata:
  hermes:
    tags: [vision, ocr, names, user-patterns]
    related_skills: [adjutant-material-ingest]
description: 波总发截图/名片/文档人名定稿的强制精读流程。裁剪放大+部件级字形描述，禁带预设提问。
category: user-patterns
---

# 截图人名/易混字精读定稿

## When to Use
波总发截图、名片、文档图片，需要提取人名/公司名/供应商名落库时。中文人名同音异形字极多，整图小字号 vision 识别错误率实测高（一次名册 11 个人名错 3 个：周平芳→周平方、商洮河→商淞河、馥锐→馥昶）。识错人名落库后波总发火纠错的成本远高于多两轮精读。

## 强制流程（顺序不可省）

1. **整图开放题首轮**：vision_analyze 只问"提取全部人名+职务"，**不带任何候选字预设**。问"是周平芳还是周XX？"会让模型顺着预设答题——实测同一模型两轮给出两个不同答案。
2. **裁剪放大**：PIL 按内容区域裁剪（人名区/供应商区分区），2× LANCZOS 放大后存 /tmp 再 vision_analyze。
3. **部件级精读提问**：对每个易混字问"描述实际看到的字形部件（偏旁/草字头有无/右部结构），不要凭常识推断"。高频坑字：芳/方、洮/淞/涛、锐/昶/韵、蕤、喆/哲。
4. **两轮不一致以放大精读为准**；仍有歧义标 `[字待核]` 落库。
5. **兜底提示**：定稿后告知波总"以工商登记/身份证为准"。

## 落库与交付

- 定稿名册写 OBS 仓拆解（表格）+ 互动日志条目；修正旧识别时用 patch 逐一替换，**grep 新旧名各验证一遍**（旧名 0 匹配才算改干净）。
- 名册/对比表交付用 matplotlib 表格截图（中文字体 STHeiti Medium.ttc），禁 markdown 表格源码——波总格式铁律。
- git push 被拒 → `git pull --rebase` → 再 push（cron 常先提交）。

## 已知误判案例

见 `references/ingest-20260829.md`（浮空平台公司名册 3 字误判全记录 + 归档缺口排查法：互动日志最后日期 vs 最新 SRC 日期不同步 = 归档缺口）。
