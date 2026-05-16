---
name: System Scanning and Migration Analysis
description: Comprehensive system scanning for project inventory, process monitoring, and migration feasibility analysis between AI assistant systems
trigger: When user asks to scan computer for projects, check system status, or analyze migration feasibility between systems
tags: [system-analysis, migration, devops, inventory]
---

## Overview
This skill provides a systematic approach to scanning computer systems for project files, analyzing AI assistant systems (like OpenClaw and Hermes), checking process status, and assessing migration feasibility between systems.

## When to Use
- User asks to "scan the computer for project files"
- Need to check system status and running processes
- Analyze migration feasibility between different AI systems
- Inventory skills, extensions, and configurations
- Assess system compatibility and migration risks

## Steps

### 1. Initial System Scan
```bash
# Scan for Git repositories
find /Users/mac -name '.git' -type d 2>/dev/null | head -20

# Scan for specific project types
find /Users/mac -name 'package.json' -type f 2>/dev/null | grep -v node_modules
find /Users/mac -name 'requirements.txt' -type f 2>/dev/null
find /Users/mac -name '*.ai' -o -name '*.ml' -o -name 'model*' -o -name 'llm*' 2>/dev/null | grep -v node_modules
```

### 2. Check System Processes
```bash
# Check for running processes related to target systems
ps aux | grep -E '(gateway|openclaw|watchdog|hermes)' | grep -v grep

# Monitor specific PIDs
ps -p 640,330,11218 -o pid,cmd,time
```

### 3. Analyze OpenClaw System
```bash
# Check OpenClaw directory structure
ls -la /Users/mac/openclaw/

# Count skill files
find /Users/mac/openclaw/skills -name '*.json' -type f | wc -l

# Count extensions
ls -d /Users/mac/openclaw/extensions/*/ 2>/dev/null | wc -l

# Check logs
ls -la /Users/mac/openclaw/logs/
```

### 4. Analyze Hermes System
```bash
# Check Hermes directory structure
ls -la /Users/mac/.hermes/

# Count skills
find /Users/mac/.hermes/skills -name 'SKILL.md' -type f | wc -l

# Check database
ls -lh /Users/mac/.hermes/hermes.db

# Check configuration
cat /Users/mac/.hermes/config.yaml | head -50
```

### 5. Skill and Extension Analysis
```bash
# Analyze skill categories (OpenClaw)
find /Users/mac/openclaw/skills -name '*.json' -type f | xargs dirname | xargs basename | sort | uniq -c

# Analyze skill content samples
for skill in telegram discord imessage whatsapp; do
  if [ -f "/Users/mac/openclaw/skills/$skill/$skill.json" ]; then
    echo "=== $skill ==="
    jq '.name, .description' "/Users/mac/openclaw/skills/$skill/$skill.json" 2>/dev/null || cat "/Users/mac/openclaw/skills/$skill/$skill.json" | head -5
  fi
done
```

### 6. Migration Feasibility Assessment
Create a structured report covering:
- **System Architecture Comparison**: JSON vs YAML, file-based vs database
- **Skill/Extension Inventory**: Count and categorization
- **Process Status**: Running services and dependencies
- **Data Storage Analysis**: Configuration formats and locations
- **Risk Assessment**: Compatibility issues, format differences
- **Migration Strategy**: Phased approach with testing

## Pitfalls to Avoid
1. **Don't assume all node_modules are projects** - filter out dependency directories
2. **Check process ownership** - ensure you're looking at the right user's processes
3. **Handle missing directories gracefully** - use conditional checks
4. **Be careful with JSON parsing** - some files may have formatting issues
5. **Consider permission issues** - some directories may require sudo

## Verification Steps
1. **Cross-check counts**: Verify skill counts from different methods
2. **Process validation**: Ensure processes are actually running (not zombie)
3. **Directory existence**: Confirm all referenced directories exist
4. **Format compatibility**: Test reading sample config files
5. **Migration test**: Try converting one sample skill as proof of concept

## Output Format
Provide a structured report with:
- **Project Statistics**: Total count, types, locations
- **System Status**: Running processes, service health
- **Inventory Details**: Skills, extensions, configurations
- **Migration Analysis**: Feasibility, challenges, recommendations
- **Action Plan**: Step-by-step migration strategy
- **Risk Assessment**: Potential issues and mitigation strategies

## Related Skills
- `codebase-inspection` for code analysis
- `github-repo-management` for Git project handling
- `devops` skills for system monitoring