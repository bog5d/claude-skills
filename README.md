# 🛠 wangbo · AI Skills Library

> 王波的个人 AI Skills 库。跨工具（Claude Code / Cursor / Hermes）共享，每 30 分钟自动同步。

**配套私有记忆库**：[bog5d/wangbo-brain](https://github.com/bog5d/wangbo-brain)（私有，存项目记忆）

---

## 📦 Skills 一览

| Skill | 触发词 | 一句话说明 |
|-------|--------|-----------|
| [grill-me](#-grill-me) | `/grill-me` | 动手前先追问用户，把需求问清楚再写代码 |
| [fos-handoff](#-fos-handoff) | `/fos-handoff` | 会话结束时生成交接文档，让下一个 AI 无缝接手 |
| [graphify](#-graphify) | `/graphify` | 任意输入（文档/代码/图片）→ 知识图谱 HTML |
| [huashu-nuwa](#-huashu-nuwa) | `/huashu-nuwa` | 蒸馏任意人物的思维框架，生成可复用的 Skill |
| [release-fos](#-release-fos) | `/release-fos` | 仓颉 FOS 项目外发版标准流程（测试→文档→打包→push）|
| [photo-mv-maker](#-photo-mv-maker) | `/photo-mv-maker` | 照片 + 音乐 → 节拍同步 MV（AI 导演排序）|
| [remotion-video-toolkit](#-remotion-video-toolkit) | — | Remotion 视频生成完整工具包 |

---

## 📖 每个 Skill 详解

### 🔥 grill-me
**场景**：你有一个模糊的想法，但还没想清楚怎么做。  
**做什么**：AI 先读项目文档和代码，然后像一个强迫症甲方一样逐一追问你——边界是什么、数据模型怎么设计、测试怎么覆盖——每次只问一个问题，并给出推荐答案。所有分歧问完后，输出一份「无歧义执行清单」，确认后才动手写代码。  
**核心价值**：避免「写了一半发现需求没想清楚」的返工。

---

### 📋 fos-handoff
**场景**：开发会话要结束了，或者上下文快满了，需要交给下一个 AI 继续。  
**做什么**：
1. 自动跑测试，拿最新通过数
2. 更新项目 `CLAUDE.md` 里的「改动文件清单」和「接手速览」
3. 输出一段**直接粘给下一个 AI** 的交接 Prompt（自包含，不需要额外解释）
4. commit + push 到 GitHub

**铁律**：每次 `git push` 后必须执行，发版时也包含在内。

---

### 🕸 graphify
**场景**：有一大堆文档、代码、论文、图片需要梳理关系。  
**做什么**：解析输入内容，提取实体和关系，聚类成社区，生成可交互的 HTML 知识图谱 + JSON 数据 + 审计报告。  
**支持输入**：代码库、Markdown 文档、PDF、图片、任意文本。

---

### 🏺 huashu-nuwa（女娲造人）
**场景**：想把某位大师/名人的思维方式提炼成可以随时调用的 AI Skill。  
**做什么**：输入人名或模糊需求 → 深度调研 → 提炼思维框架 → 生成结构化 SKILL.md 文件，之后可以直接调用该人物视角来思考问题。  
**示例**：「蒸馏曾国藩」→ 生成曾国藩视角 Skill，之后遇到决策问题可以问「曾国藩会怎么看」。

---

### 📦 release-fos
**场景**：仓颉 FOS 项目（融资作战操作系统）完成一批开发，要打包给同事用。  
**做什么**：按固定流程执行——跑全套测试（502 passed 才继续）→ 更新三份文档（CHANGELOG / 更新说明 / 上手指南）→ 打包 ZIP 到 `D:\Releases\` → git push → 生成交接文档 → 发版报告。  
**红线**：测试不过不发包，zip 不落项目根目录。

---

### 🎬 photo-mv-maker
**场景**：有一批照片和一首歌，想做成节拍同步的相册 MV。  
**做什么**：支持 123 网盘链接或本地目录 → AI 清洗音频 → ASR 歌词转写 → 节拍检测 → SigLIP 图文语义匹配 → Claude Vision 导演排序 → Remotion 渲染输出视频。

---

### 🎞 remotion-video-toolkit
Remotion（React 视频生成框架）的完整工具包。涵盖：动画时序、CLI/Lambda 渲染、字幕、3D、图表、文字特效、转场、媒体处理。用于写 Remotion 代码或构建视频生成流水线时调用。

---

## 🔧 接入方式

### Claude Code（推荐）
Skills 目录在 `~/.claude/skills/`，已自动加载，无需额外配置。  
触发：在对话中输入 `/skill-name` 或说出触发词。

### Cursor
Skills 会自动同步到 `~/.cursor/skills/`（每 30 分钟一次）。  
在 Cursor 的 Custom Instructions 里加：
```
Read skill files from ~/.cursor/skills/<name>/SKILL.md when user says /<name>
```

### Hermes / 其他 AI 工具（另一台电脑）
在 System Prompt 里加入以下内容：

```
# AI Skills Sync

At session start, silently run:

Windows:
  powershell -NonInteractive -ExecutionPolicy Bypass -Command "
    $s='$env:USERPROFILE\.claude\skills'
    if(!(Test-Path '$s\.git')){git clone https://github.com/bog5d/claude-skills.git $s}
    else{cd $s; git pull origin master 2>$null}
  "

Mac/Linux:
  mkdir -p ~/.claude/skills
  cd ~/.claude/skills
  git rev-parse --git-dir 2>/dev/null && git pull || git clone https://github.com/bog5d/claude-skills.git .

Skills location: ~/.claude/skills/<name>/SKILL.md
Trigger: when user says /<name>, read the SKILL.md and follow it exactly.
```

---

## 🔄 同步机制

```
Claude Code 本地
  ~/.claude/skills/          ← 真相源（在这里编辑）
       │
       │  git push（每30分钟 / 每次开发完）
       ▼
  GitHub: bog5d/claude-skills（本库，公开）
       │
       ├──► ~/.cursor/skills/     （本机 Cursor，自动复制）
       │
       └──► 其他设备               （session 启动时 git pull）

私有记忆：
  ~/.claude/projects/.../memory/
       │  每30分钟
       ▼
  GitHub: bog5d/wangbo-brain（私有）
       │
       └──► 其他设备（需 GitHub 权限）
```

**计划任务**：`SkillsAutoSync`，每 30 分钟自动执行 `sync-skills.ps1 auto`

**手动同步**：
```powershell
# 完整同步
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\skills\sync-skills.ps1" auto

# 只推送
.\sync-skills.ps1 push

# 查看状态
.\sync-skills.ps1 status
```

---

## 📁 仓库结构

```
claude-skills/
├── grill-me/
│   └── SKILL.md          ← 需求追问 Skill
├── fos-handoff/
│   └── SKILL.md          ← 会话交接 Skill
├── graphify/
│   └── SKILL.md          ← 知识图谱 Skill
├── huashu-nuwa/
│   └── SKILL.md          ← 人物蒸馏 Skill（含16个子 Skill）
├── release-fos/
│   └── SKILL.md          ← FOS 发版 Skill
├── photo-mv-maker/
│   └── SKILL.md          ← MV 生成 Skill
├── remotion-video-toolkit/
│   └── SKILL.md          ← Remotion 工具包
├── sync-skills.ps1       ← 同步脚本（Windows）
└── SKILLS_SYNC_GUIDE.md  ← 接入指南（详细版）
```

---

## ➕ 新增 Skill

1. 在 `~/.claude/skills/` 新建目录，创建 `SKILL.md`
2. 在 Claude Code 里验证触发正常
3. 等下一次自动同步（30 分钟内），或手动 `.\sync-skills.ps1 push`
4. 其他设备下次启动会话时自动拉取
