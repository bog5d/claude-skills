# Claude Code 内置 Skills 参考

> 这些 skills 由 Anthropic 平台提供，Claude Code 启动后直接可用，无需 git 克隆。
> 通过 `/skill-name` 或 Skill tool 调用。

---

## session-start-hook

**触发条件：** 用户想为 Claude Code 配置会话启动时自动执行的命令（如 git pull、环境检查）

**功能：** 在 `~/.claude/settings.json` 中添加 SessionStart 钩子，每次 Claude Code 启动时自动执行指定命令。

**典型用途：**
```bash
# 自动拉取最新 skills
cd ~/.claude/skills && git pull origin master 2>/dev/null || true
```

---

## update-config

**触发条件：** 用户说"以后每次X都要Y"、"允许X命令"、"添加权限"、"修改设置"

**功能：** 修改 `settings.json` 或 `settings.local.json`，配置 hooks、permissions、env vars。

---

## keybindings-help

**触发条件：** 用户想自定义快捷键、重绑定按键、添加组合键

**功能：** 修改 `~/.claude/keybindings.json`，支持单键、组合键（chord）绑定。

---

## simplify

**触发条件：** 代码修改完成后，想做质量审查、去除冗余、提升可读性

**功能：** 审查改动代码，检查可复用性、质量和效率，修复发现的问题。

---

## fewer-permission-prompts

**触发条件：** 用户频繁遇到权限确认弹窗，想减少打断

**功能：** 扫描会话记录中常见的只读 Bash / MCP 工具调用，生成 allowlist 写入项目 `.claude/settings.json`。

---

## loop

**触发条件：** 用户想定期重复执行某个任务（"每5分钟检查一次"、"循环运行"）

**功能：** 以指定时间间隔（默认10分钟）循环执行一个命令或 skill。

**格式：** `/loop 5m /some-skill`

---

## claude-api

**触发条件：** 代码中 import anthropic、用户问 Claude API/SDK、需要构建 Claude 应用

**功能：** 构建、调试、优化 Claude API / Anthropic SDK 应用，包含 prompt caching 最佳实践。支持模型版本迁移（4.5→4.6→4.7）。

---

## init

**触发条件：** 项目目录没有 CLAUDE.md，或用户说"初始化项目文档"

**功能：** 扫描代码库，生成 `CLAUDE.md`，记录项目结构、构建命令、架构说明。

---

## review

**触发条件：** 用户说"帮我 review PR"、"审查这个 PR"

**功能：** 对当前分支或指定 PR 做代码审查，输出问题列表和改进建议。

---

## security-review

**触发条件：** 用户说"安全审查"、"检查安全漏洞"、"review 安全性"

**功能：** 审查当前分支的变更，检查 OWASP Top 10、注入漏洞、认证问题等安全风险。

---

## 使用说明

这些 skills 的触发由 Claude Code 平台注入，不存储于此仓库中，此文档仅为**跨 Agent 参考用途**。
