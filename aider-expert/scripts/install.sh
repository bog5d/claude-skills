#!/bin/bash
# Aider-Expert Skill 安装脚本
# 创建桥接脚本

BRIDGE_SCRIPT="$HOME/aider_workspace/bridge.py"

mkdir -p "$HOME/aider_workspace"

if [ ! -f "$BRIDGE_SCRIPT" ]; then
    echo "正在创建桥接脚本: $BRIDGE_SCRIPT"
    echo 'import sys, subprocess, json, os

def main():
    raw_cmd = " ".join(sys.argv[1:])
    task = json.dumps({"task": raw_cmd})
    work_dir = os.path.expanduser("~/Cangjie_OBS_Notes")

    cmd = f"cd {work_dir} && aider --model claude-sonnet-4-20250514 --no-auto-commits --yes '"

<｜DSML｜parameter name="content" string="true">#!/bin/bash
# Aider-Expert Skill 安装脚本
# 创建桥接脚本

BRIDGE_SCRIPT="$HOME/aider_workspace/bridge.py"

mkdir -p "$HOME/aider_workspace"
# 在下一轮继续安装