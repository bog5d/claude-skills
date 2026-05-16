# claude-skills · AI Agent Skill Hub

> 波总（Bog Wang）的跨平台 AI Skills 仓库。
> 任何 AI Agent（Claude Code / Cursor / Copilot / Hermes / Codex）都能直接使用、贡献、拉取。

---

## 这是什么

这是一个 **AI Skill 共享仓库**。里面每个 skill 是一个独立目录：

```
skill-name/
├── SKILL.md          ← 核心：触发条件 + 步骤 + 铁律
├── scripts/          ← 可执行脚本
├── references/       ← 参考文档
├── templates/        ← 模板文件
└── assets/           ← 静态资源
```

每个 skill 描述了一件 AI 应该怎么做的事——从「如何调试 bug」到「如何生成 PPT」。

---

## 快速开始

### 任何 AI Agent 克隆后即可使用

```bash
git clone https://github.com/bog5d/claude-skills.git ~/.claude/skills
```

克隆后，读取你想用的 skill：

```
读取 ~/.claude/skills/<category>/<skill-name>/SKILL.md，按里面的步骤执行。
```

### Skill 格式约定

每个 `SKILL.md` 包含：

```yaml
---
name: skill-name
description: 一句话说明（AI 用来匹配触发条件）
category: 所属分类
---

# Skill 标题

## 触发条件
什么时候应该加载这个 skill

## 步骤
1. 第一步做什么（含具体命令）
2. 第二步...
...

## 铁律 / 已知坑
绝对不能做的事、已知会踩的坑
```

---

## 分类索引

| 分类 | 说明 | 数 |
|------|------|----|
| apple | macOS 原生集成 | 4 |
| autonomous-ai-agents | 子 Agent 调度 | 4 |
| creative | 创意生成/视觉 | 7 |
| data-science | Jupyter | 1 |
| devops | 系统运维 | 16 |
| email | 邮件 | 1 |
| gaming | 游戏 | 2 |
| github | GitHub 工作流 | 6 |
| leisure | 休闲 | 1 |
| mcp | MCP 协议 | 3 |
| media | 媒体处理 | 4 |
| mlops | ML 全栈 | 22 |
| note-taking | 笔记 | 1 |
| productivity | 生产力 | 7 |
| project-analysis | 项目分析 | 2 |
| red-teaming | 红队 | 1 |
| research | 论文/监控 | 5 |
| smart-home | 智能家居 | 1 |
| social-media | 社交 | 1 |
| software-development | 软件工程 | 24 |
| user-patterns | 波总专用 | 5 |

**总计：126 个 skill（2026-05-16）**

---

## 使用规则（所有 AI Agent 必须遵守）

### 1. 加载优先级
接到任务 → 先扫 skill 目录匹配 → 有就加载 SKILL.md 严格按步骤执行 → 没有就正常推理

### 2. 贡献新 Skill
发现可复用工作流后：
```bash
mkdir -p ~/.claude/skills/<category>/<new-skill>/
# 写 SKILL.md（遵循格式）
# git add + commit + push
```

### 3. 修改已有 Skill
执行 skill 时发现步骤过时/有坑 → **立即修复**，不要等。修改后 commit + push。

### 4. 同步协议
- 仓库每 30 分钟自动推送到 GitHub
- 任何 Agent 开机：`git pull` 获取最新
- **禁止存 API key 或密码**

### 5. 质量铁律
- 必须有「触发条件」和「铁律/坑」
- 步骤必须可执行，不含"根据需要调整"
- 连续执行失败两次 → 标记 `⚠️ BROKEN`

---

## 与私有记忆库的关系

- **claude-skills（公开）**：存「怎么做」
- **[wangbo-brain](https://github.com/bog5d/wangbo-brain)（私有）**：存「波总说了什么 / 项目状态」
- 配套使用：先读 wangbo-brain 了解上下文，再用 claude-skills 执行

---

## 自动化

- **cron**：每 30 分钟三端比对 → 推 GitHub
- **Tysk 协议**：GitHub ↔ Hermes 双向同步，任何 AI 可接盘

*最后更新：2026-05-16 · 当值：Hermes*
