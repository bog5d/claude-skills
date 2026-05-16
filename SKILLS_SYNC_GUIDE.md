# Skills 同步指南

GitHub 仓库：https://github.com/bog5d/claude-skills  
本地路径（Windows）：`%USERPROFILE%\.claude\skills\`

---

## 各工具接入方式

### Claude Code（已内置自动同步）
- SessionStart → 自动 `git pull`
- 写入 skills 目录 → 自动 `git commit + push`
- 无需手动操作

### Cursor（已自动同步）
- 个人 skills 目录：`%USERPROFILE%\.cursor\skills\`
- 每30分钟通过计划任务自动更新
- 新 skill 创建后30分钟内自动出现

### Hermes / Cherry Studio / 其他 Agent 工具
将下方 **System Prompt 片段**粘贴进工具的 System Prompt 或 Custom Instructions。

### Windows 计划任务（已注册）
- 任务名：`SkillsAutoSync`
- 频率：每30分钟
- 手动运行：`powershell -File "%USERPROFILE%\.claude\skills\sync-skills.ps1" auto`

---

## 通用 Agent System Prompt 片段

```
# My Skills Library

I maintain a personal skills library on GitHub: https://github.com/bog5d/claude-skills

**How to sync at session start (run silently):**
- Windows: powershell -NonInteractive -ExecutionPolicy Bypass -Command "cd $env:USERPROFILE\.claude\skills; git pull origin master 2>$null"
- Mac/Linux: cd ~/.claude/skills && git pull origin master 2>/dev/null || true

**Skill format:** Each skill is a directory with a SKILL.md file. The frontmatter contains:
- name: skill name
- description: when to activate
- trigger: slash command (optional)

**How to apply skills:** When I say "use skill [name]" or the trigger condition matches, read the corresponding SKILL.md and follow its instructions.

**Available skills (auto-updated from GitHub):**
- graphify: any input → knowledge graph → HTML + JSON + audit report (/graphify)
- huashu-nuwa: distill any person's thinking framework into a reusable Skill (/huashu-nuwa)
- [更多 skills 在 GitHub 仓库中查看]

**When a new skill is created:** Run the following to push to GitHub:
- Windows: powershell -File "%USERPROFILE%\.claude\skills\sync-skills.ps1" push
- Mac/Linux: cd ~/.claude/skills && git add -A && git commit -m "new skill" && git push origin master
```

---

## 手动同步命令

```powershell
# 完整同步（push 本地变更 + pull 最新 + 同步到 Cursor）
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\skills\sync-skills.ps1" auto

# 只推送本地变更到 GitHub
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\skills\sync-skills.ps1" push

# 从 GitHub 拉取最新并同步到 Cursor
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\skills\sync-skills.ps1" pull

# 查看同步状态
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\skills\sync-skills.ps1" status
```
