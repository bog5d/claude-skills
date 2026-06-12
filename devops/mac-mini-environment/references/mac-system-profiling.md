---
name: mac-system-profiling
description: Scan macOS system configuration and installed software inventory — hardware specs, disk usage, /Applications listing, Homebrew packages (leaves + casks), and key dev tool versions.
trigger: User says "统计软件"、"配置如何"、"系统信息"、"how many apps"、"machine specs"
category: devops
---

# macOS System Profiling

Quick one-shot scan of a Mac's hardware specs, installed apps, and dev environment.

## Steps

1. **System & hardware**
```bash
echo "=== 系统 ===" && sw_vers
echo "=== 硬件 ==="
sysctl -n hw.memsize | awk '{printf "内存: %.1f GB\n", $1/1073741824}'
sysctl -n hw.ncpu | xargs echo "CPU 核心数:"
sysctl -n machdep.cpu.brand_string
```

2. **Disk**
```bash
df -h / | tail -1 | awk '{print "总空间:", $2, "已用:", $3, "可用:", $4, "(" $5 ")"}'
```

3. **/Applications inventory** (exclude Apple system apps)
```bash
echo "=== /Applications ==="
ls -1 /Applications/ | grep -vE "^(System|Utilities)" | tee /tmp/apps.txt
wc -l < /tmp/apps.txt | xargs echo "数量:"
```

4. **Homebrew packages**
```bash
echo "=== brew leaves ==="
brew leaves
echo "=== brew casks ==="
brew list --cask
```

5. **Dev tool versions**
```bash
python3 --version 2>/dev/null
node --version 2>/dev/null
go version 2>/dev/null
docker --version 2>/dev/null
xcrun swift --version 2>/dev/null | head -1
```

## Present as

Group into three sections:
- **系统配置** (OS, CPU, RAM, disk)
- **已安装软件统计** (table: /Applications count, brew leaves count, brew casks count)
- **开发环境** (list with versions)

## Notes

- `mdfind` (Spotlight) is **unreliable in sandbox** — do NOT use it. Stick to `/Applications` + `brew` for accurate counts.
- Aider routing (`bridge_cmd.py`) is **not suitable** for info-only tasks; it expects code-gen work. Use direct terminal for data collection.
- Core system tools (Safari, etc.) show in /Applications — flag them if user wants "only user-installed" vs total.
