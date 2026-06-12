---
name: hermes-audit-report
description: Use when generating an audit/review report for Hermes agent — hardware scan + project structure analysis merged into a single MD file
---

# Hermes Audit Report Generation

## Trigger
User asks to scan/audit/review a Mac and/or Hermes agent project, and output a markdown report.

## Steps

1. **Hardware scan** — collect comprehensive Mac specs:
   ```
   system_profiler SPHardwareDataType
   system_profiler SPStorageDataType
   system_profiler SPNetworkDataType
   sw_vers
   uname -a
   sysctl hw.*
   sysctl machdep.cpu.*
   ```

2. **Hermes project structure scan**:
   ```bash
   cd /Users/mac/.hermes/hermes-agent
   ls -la
   find . -maxdepth 2 -name "*.py" | head -80
   git log --oneline --count
   git log --oneline | wc -l
   find tests/ -name "test_*.py" | wc -l
   ```

3. **Docker/environment check**:
   ```bash
   docker version
   docker ps
   docker info 2>&1 | head -5
   ```

4. **Generate output** — write MD report to `~/.hermes/cron/output/hermes-audit-report.md`

## Expected Report Sections
- **Hardware** — CPU, RAM, storage, GPU, cache hierarchy
- **System** — OS version, kernel, uptime, load average
- **Network** — active interfaces, MAC addresses, link status
- **Hermes Project** — file count, commit count, test count, architecture overview
- **Status** — Docker status, known issues, bottlenecks
- **Recommendations** — based on findings (RAM pressure, Docker, etc.)