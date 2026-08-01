---
name: project-cairn
description: Use when 项目含 cairn/ 目录或要求经验毕业/做个体检。五步循环沉淀经验至 Obsidian。
category: user-patterns
trigger: 初始化 project-cairn, cairn/ 目录存在, 把这条经验毕业, 做个体检, 经验沉淀
priority: high
---

# Project Cairn — 经验知识化 Agent Skill

> 目标：高体感、低阻力地把踩坑经验、关键决策、探索成果沉淀为可复用知识，并流转到 Obsidian 全局知识库（波总的知识库：`~/AI_Workspaces/Cangjie_OBS_Notes`，私有 GitHub 仓库自动同步）。

## 1. 核心工作流：五步循环

1. **记日志** `cairn/log.md` — 朝后看：只记实质进展摘要（做了什么、定了什么）。单条 ≤20 行，轻快。细节用"指针"（相对链接）指向 topics/ 文档。
2. **维护路线图** `cairn/roadmap.md` — 朝前看：只维护三类信息【里程碑】【当前焦点】【未解决的问题】。不写长篇。
3. **提炼主题结论** `cairn/topics/` — 解决了一个问题或形成稳定结论时，写入主题文档（格式见 §3）。
4. **知识毕业**（征求同意后推送 Obsidian）— 经验验证且具备跨项目复用价值时，必须先提议："这条经验具有通用价值，是否将其毕业到 Obsidian 知识库？" 用户点头后才执行。
5. **开工前回流** — 每次开启新任务/遇到新问题前，先查：当前项目 `cairn/topics/` + Obsidian 全局知识库的 Index。找到现成结论直接应用，避免重复踩坑。

## 2. 目录规范（项目侧）

与真实工程代码物理隔离：

```
cairn/
├── log.md          # 朝后看：进展摘要，指针链接
├── roadmap.md      # 朝前看：里程碑/当前焦点/未解决问题
├── reference/      # 外部输入原始资料（甲方规则、模板），只归档不改写
└── topics/         # 主题文档：踩坑排查、决策方案（OKF 规范）
```

## 3. topics/ 文档格式（OKF v0.2 对齐）

顶部 YAML Front Matter，正文普通 Markdown：

```yaml
---
type: Topic            # Topic | Decision | Postmortem | Playbook
title: 一句话主题
description: 这个主题解决什么问题
status: stable          # draft | stable | archived
sources:                # 来源指针，可验证
  - 2026-08-01 修复XX日志.md
verified: 2026-08-01   # 最后验证日期
updated: 2026-08-01
tags: [踩坑, 经验]
---
# 标题

## 问题
## 根因
## 解法（可执行的步骤）
## 验证（怎么确认有效）
## 相关链接（双链/相对路径）
```

## 4. 知识毕业规则

1. 必须先提议并等用户确认，禁止擅自推送。
2. 剥离当前项目特有的局部/私密信息。
3. 整合成独立可阅读的 Obsidian 笔记（放 `~/AI_Workspaces/Cangjie_OBS_Notes` 合适分类目录）。
4. 运用双链建立连接，更新全局 Index（`obs-wiki/wiki/index.md` 或知识库对应索引）。
5. 记录经验最初来自哪个项目；后续结论有变时更新原笔记，不复制冗余副本。
6. 毕业动作完成后：`cd ~/AI_Workspaces/Cangjie_OBS_Notes && git add <具体文件> && git commit -m "cairn: <主题>" && git push origin main`。

## 5. 触发词

- **初始化 project-cairn**：开启对话引导，确认项目一句话定位及 Obsidian 绝对路径，写入 `cairn/agent.md`。
- **把这条经验毕业**：立刻把当前讨论的结论执行"知识毕业"流程（先确认 → 剥离 → 写笔记 → 更新索引 → push）。
- **做个体检**：主动扫描 cairn/ 目录，检查：主题文档是否相互冲突、指针链接是否失效、哪些经验一直压在项目里未处理，汇报。

## 6. 陷阱

- log.md 不是流水账：单条 ≤20 行，细节进 topics/。
- 知识毕业必须征求同意——用户明确要求"只有我点头确认后"。
- 指针用相对路径或 Obsidian 双链，绝对路径会失效。
- topics/ 不写私密信息（密钥、账号、合同敏感条款），毕业前剥离。
- OKF 的 sources 必须可验证（文件名/时间戳），禁止编造来源。
- 修改 Cangjie_OBS_Notes 后必须 git push（波总数据同步铁律），但只 add 具体文件，禁止 git add -A 全量提交。

## 7. 与现有系统衔接

- Hermes 技能体系：本技能即 Hermes Skill（SKILL.md），与 claude-skills 仓库跨 AI 共享。
- 副官系统：`~/.hermes/adjutant/repo/hermes-adjutant` 管任务状态；cairn 管经验知识。任务完成后的经验沉淀走本技能。
- Obsidian 知识库：`~/AI_Workspaces/Cangjie_OBS_Notes`（已配置自动 git pull cron），知识毕业目标地。
