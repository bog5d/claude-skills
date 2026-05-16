# claude-skills · AI Agent 接盘手册

> **这是你作为 AI Agent 接入波总工作环境的第一份文档。**
> 读完本文，你就知道：有哪些 skills、记忆存在哪、怎么同步、怎么贡献。

---

## 两仓库体系

| 仓库 | 地址 | 权限 | 存什么 |
|------|------|------|--------|
| **claude-skills** | https://github.com/bog5d/claude-skills | 公开 | 怎么做（SOP / Skill 流程） |
| **wangbo-brain** | https://github.com/bog5d/wangbo-brain | 私有 | 波总说了什么 / 项目状态 / 偏好记忆 |

**铁律：先读记忆（wangbo-brain），再用 skills（claude-skills）执行。**

---

## 新 Agent 接盘 · 5步启动协议

```bash
# 步骤1：克隆 skills（公开，任何 Agent 可执行）
git clone https://github.com/bog5d/claude-skills.git ~/.claude/skills

# 步骤2：克隆记忆库（需要 GitHub 私有仓库访问权限）
git clone https://github.com/bog5d/wangbo-brain.git ~/.claude/memory

# 步骤3：读取核心记忆（了解项目状态和波总偏好）
cat ~/.claude/memory/README.md
cat ~/.claude/memory/current-context.md   # 如存在

# 步骤4：确认 skills 最新
cd ~/.claude/skills && git pull origin master

# 步骤5：告知波总接盘成功，并汇报当前 skill 数量
echo "接盘完成"
```

> 如无法访问 wangbo-brain（无私有仓库权限），跳过步骤2-3，告知波总即可。

---

## 每次会话同步协议

### 会话开始时（SessionStart）

```bash
# 拉取最新 skills
cd ~/.claude/skills && git pull origin master 2>/dev/null || true

# 拉取最新记忆
cd ~/.claude/memory && git pull origin main 2>/dev/null || true
```

### 会话结束时 / 产生重要变更时

```bash
# 推送 skills 变更（如新增或修改了 skill）
cd ~/.claude/skills && git add -A && git commit -m "sync: $(date +%Y%m%d-%H%M%S)" && git push origin master

# 推送记忆变更（如有新的上下文/决策记录）
cd ~/.claude/memory && git add -A && git commit -m "memory: $(date +%Y%m%d-%H%M%S)" && git push origin main
```

---

## Agent 专属配置

### Claude Code

Claude Code 有**平台级内置 Skills**（无需 git，直接可用）：

| Skill | 触发方式 | 功能 |
|-------|----------|------|
| `session-start-hook` | `/session-start-hook` | 配置 SessionStart 钩子 |
| `update-config` | `/update-config` | 修改 settings.json / hooks |
| `keybindings-help` | `/keybindings-help` | 快捷键配置 |
| `simplify` | `/simplify` | 代码质量审查与重构 |
| `fewer-permission-prompts` | `/fewer-permission-prompts` | 减少权限弹窗 |
| `loop` | `/loop` | 定时循环任务 |
| `claude-api` | `/claude-api` | Anthropic SDK 开发 |
| `init` | `/init` | 初始化 CLAUDE.md |
| `review` | `/review` | PR 代码审查 |
| `security-review` | `/security-review` | 安全审查 |

详细文档：[claude-code/SKILLS.md](claude-code/SKILLS.md)

**推荐的 SessionStart 钩子配置**（在 `~/.claude/settings.json` 中添加）：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "cd ~/.claude/skills && git pull origin master 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

### Cursor

- Skills 目录：`%USERPROFILE%\.cursor\skills\`（Windows）或 `~/.cursor/skills/`（Mac）
- 每30分钟通过计划任务自动同步
- 在 System Prompt 中添加：`Read ~/.claude/skills/**/ 匹配任务后加载 SKILL.md`

### Hermes

- Hermes 已配置每30分钟 cron 自动同步
- 路径：`~/.claude/skills/`
- 记忆同步：已集成 wangbo-brain 双向协议

---

## Skills 目录总览

**当前：126 个 skills，27 个分类（2026-05-16）**

| 分类 | 数量 | 代表 Skill |
|------|------|-----------|
| software-development | 24 | systematic-debugging, plan, prototype |
| mlops | 22 | jupyter-live-kernel, 模型训练流程 |
| devops | 17 | handoff, multi-profile-setup |
| creative | 7 | manim-video, p5js, ascii-art |
| productivity | 7 | 任务规划, 会议记录 |
| github | 6 | PR 工作流, code review |
| user-patterns | 5 | 波总专用偏好 |
| research | 5 | 论文阅读, 监控 |
| apple | 4 | iMessage, Apple Notes |
| autonomous-ai-agents | 4 | 子 Agent 调度 |
| media | 4 | 视频处理 |
| claude-code | 10 | Claude Code 内置 Skills（见上方表格） |
| 其他13类 | ~10 | 见 README.md |

完整列表：[README.md](README.md)

---

## 贡献新 Skill

```bash
mkdir -p ~/.claude/skills/<category>/<skill-name>/
# 写 SKILL.md（包含：触发条件 / 步骤 / 铁律）
cd ~/.claude/skills && git add -A && git commit -m "add skill: <skill-name>" && git push origin master
```

**质量铁律：**
- 必须有「触发条件」和「铁律/坑」
- 步骤必须可执行，不含"根据需要调整"
- 执行失败两次 → 在 SKILL.md 顶部标记 `⚠️ BROKEN`

---

## 禁止事项

- ❌ 禁止在此仓库存 API key、密码、token
- ❌ 禁止修改他人 skill 而不 commit
- ❌ 禁止将私有记忆（wangbo-brain 内容）推送至此公开仓库

---

*最后更新：2026-05-16 · 当值：Claude Code*
