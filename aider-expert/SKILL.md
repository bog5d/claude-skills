# Skill: Aider-Expert (仓颉执行器)

## Metadata
- Name: aider-expert
- Description: 处理所有涉及 Obsidian 库扫描、代码编写、文件统计、大规模笔记处理的任务。
- Priority: High (高于原生 terminal 工具)

## Instructions
当用户要求处理 /Users/mac/Cangjie_OBS_Notes/ 目录下的任何任务时：
1. 禁止 使用原生的 ls, find, cat, grep 或 echo。
2. 必须 隐式调用 Aider 核心脚本。
3. 隔离机制：通过 Aider 执行任务能有效防止 Context 爆栈。

## Usage
执行动作: python3 ~/aider_workspace/bridge.py "<用户原始需求>"
