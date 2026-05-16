---
name: handoff
title: "工作交接协议"
description: "会话结束前/切换工具前生成交接文档，记录项目结构、已完成决策、遗留问题、下一步指令。任何AI可无缝接盘。"
trigger: "当波总说'交接'、'handoff'、'收尾'、'总结一下当前状态'、'给下一个会话'时，或会话自然结束前"
---

# handoff — 工作交接协议

## 核心逻辑

确保工作状态不丢失——任何 AI（Claude、Cursor、下一个 Hermes 会话）读完 handoff.md 就能接盘。

## Phase 1: 信息采集（并行）

三个维度同时采集：

```python
# 1. 项目结构
search_files(pattern="*", target="files", path=项目根目录, limit=100)

# 2. 任务状态
todo()  # 当前 todo list

# 3. Git 状态
terminal("git status --short && git log --oneline -10")
```

## Phase 2: 生成 handoff.md

文件结构：

```markdown
# Handoff — YYYY-MM-DD HH:MM

## 接手方
[Claude / Cursor / 下一个 Hermes 会话 / Aider]

## 项目状态
- 当前分支 / 最后 commit
- 关键文件改动

## 已完成决策
1. ...
2. ...

## 遗留问题（Pending Issues）
| 问题 | 严重程度 | 备注 |
|------|---------|------|
| ... | high/medium/low | ... |

## 下一步具体指令
1. ...
2. ...

## 环境信息
- 工作目录
- 活跃服务/端口
- 需要设置的 API Key
```

## Phase 3: 写入根目录

```python
write_file(path="handoff.md", content=...)
```

## Phase 4: 确认输出

告知波总文件路径和核心内容摘要。

## Pitfalls

- 不要写废话——接手方 AI 需要的是可执行指令，不是叙事散文
- 遗留问题必须标注严重程度，让接手方知道先处理什么
- 环境信息要具体到端口号、进程名，不要"服务器在运行"这种模糊描述
