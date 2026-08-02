---
name: skill-porter
description: 导出/导入/分享/同步 Hermes Skills。use `hermes-skill` command.
category: devops
---

# Skill Porter — hermes-skill

脚本: `/Users/mac/.hermes/scripts/skill_porter.py`
命令: `~/.local/bin/hermes-skill` (symlink)

## 四个命令

```bash
hermes-skill list                              # 列出所有 Skills
hermes-skill export <name> [-o /tmp]           # 导出为 .tar.gz
hermes-skill import <file.tar.gz> [-c cat] [-f] # 导入
hermes-skill share <name>                       # 公网分享 (localhost.run)
hermes-skill sync <src_prof> <dst_prof> [--skill name] [--dry-run]
```

## 打包格式

.tar.gz 内含: `porter_manifest.json` + `<skill>/SKILL.md` + references/scripts/...

## 同步策略

基于 mtime: 源更新才覆盖，不删除目标。跳过 .archive/.disabled_archive。
