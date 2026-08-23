---
name: multi-agent-project-workspace
version: 1.0.0
author: ox-alpha
license: internal
description: 波总要为项目建多AI共享工作区时用：标准骨架+归档铁律+台账+转写双轨制+接手协议。
tags: [workspace, multi-agent, asr, project-governance]
related_skills: [adjutant-brain-dump, handoff, meeting-intelligence]
---

# 多Agent项目工作区（Multi-Agent Project Workspace）

## When to Use（触发条件）
- 波总为长周期项目（BP、尽调、研究、融资材料包）建文件夹，说「建立规则」「多个Agent都会接手」「我不停扔材料」「统一采集入口」
- 接手任何已含 `_RULES.md` 的项目文件夹时（先读规则再动手，见下方接手协议）
- 已知实例：`~/Desktop/上海交大项目/`（临近空间算力创业BP）

## 标准动作（新建工作区）
1. `mkdir -p` 目录骨架（见下）
2. 用 `templates/_RULES_template.md` 和 `templates/_LEDGER_starter.md` 生成两个根文件（按项目改背景节和来源枚举）
3. 把文件夹里已有文件按命名规范归档进 `01_原始材料/<来源>/`
4. 台账登记每一笔
5. 向波总汇报：结构图 + 使用方法（怎么扔料、怎么提它、换AI怎么接手）

## 目录骨架（固定，不随项目变）
```
00_INBOX/            ← 唯一入口，一切新材料先落这里
01_原始材料/          ← 只读保护区！按来源分子目录（如 交大方/口述与会议/外部参考）
02_分析与洞察/        ← AI产出区（市场/技术/商业模式等子目录）
03_BP工程/            ← 交付物区（素材库/文案草稿/大纲与版本；非BP项目可改名03_交付物）
99_ARCHIVE/           ← 废弃区，只进不出
_RULES.md             ← 规则，任何Agent接手必读
_LEDGER.md            ← 台账，谁动了什么
```

## 七条铁律
1. 新材料只进 `00_INBOX/`；波总乱放进别的目录不算违规，当值Agent负责归位
2. `01_原始材料/` 只读；要做批注/摘录就产出新文件放 `02_`
3. 命名死格式 `YYYYMMDD_来源_描述.ext`；来源枚举按项目定义但必须写死在 _RULES.md（例：交大方/波总/ox/外部/其他AI）
4. `_LEDGER.md` 只追加、不修改他人条目；收工前必更新
5. 永不物理删除，不要的移 `99_ARCHIVE/`
6. 发现规则缺口 → 台账 `[RULE-GAP]` 区写建议等波总拍板，禁止私改规则
7. 涉及数字必须注明出处文件，禁止无出处编造

## 口述/录音转写双轨制（最高频场景）
- **原文轨**：逐字全文存 `01_原始材料/口述与会议/`，一字不改。⚠️禁止写"完整内容见原消息"式占位符偷懒——2026-08-23 曾当场犯此错返工
- **整理稿轨**：另出修正版放 `02_` 对应子目录，同名不同目录，开头注明出处关系
- 拿不准的词标 `【？】`，并在文末集中列「待核实清单」
- 说话人标签（说话人1/2）在ASR里经常错乱 → 按内容逻辑重新归属，整理稿开头给「参会角色推断表」
- ASR同音错字高频映射表见 `references/asr-noise-glossary.md`（整理前先扫一遍能省一半猜谜时间）

## 接手协议（任何Agent，进场/退场各一件事）
- 进场：读 `_RULES.md` 全文 + `_LEDGER.md` 尾部20行（最新状态）
- 退场：台账追加一行（动作/产出/下一步建议），并刷新 `_RULES.md` 的「当前状态」节

## 边界（别越界）
- 单条任务记录 → `adjutant-brain-dump`；会话结束交接文档 → `handoff`；会议录音入库SQLite → `meeting-intelligence`
- 本skill只管「项目级持续工作区的治理规则」，三者不互斥
