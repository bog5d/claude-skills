---
name: skill-porter
description: Export/import Hermes skills as tar.gz archives.
---

# skill-porter — Skills 打包/迁移工具

## 概述

`~/.hermes/scripts/skill_porter.py` 提供 Hermes Skills 的导出/导入能力。

- **导出**：将单个 Skill（含 SKILL.md + references/ + scripts/ + tests/）打包为 `.tar.gz`，内含 `porter_manifest.json` 元信息
- **导入**：从 `.tar.gz` 还原到指定 profile，支持 category 指定和强制覆盖
- **列表**：列出当前 profile 所有可导出的 Skills

## 用法

```bash
# 列出所有 Skills
python3 ~/.hermes/scripts/skill_porter.py list [-p her-m2]

# 导出到 ~/.hermes/exports/
python3 ~/.hermes/scripts/skill_porter.py export <skill_name>

# 导出到指定目录
python3 ~/.hermes/scripts/skill_porter.py export <skill_name> -o /tmp

# 导入
python3 ~/.hermes/scripts/skill_porter.py import <archive.tar.gz> [-p her-m2]

# 强制覆盖已有 skill
python3 ~/.hermes/scripts/skill_porter.py import <archive.tar.gz> -f

# 指定导入分类目录
python3 ~/.hermes/scripts/skill_porter.py import <archive.tar.gz> -c social-media

# JSON 输出（机器可读）
python3 ~/.hermes/scripts/skill_porter.py list --json
```

## 打包格式

`.tar.gz` 结构：
```
porter_manifest.json        # 元信息：导出时间、文件列表、大小、描述
<skill_name>/               # 完整 skill 目录
  SKILL.md
  references/...            # 可选
  scripts/...               # 可选
  tests/...                 # 可选
```

## 设计原则

- Python 3.8+ 兼容（无 `|` union 语法、无 `filter="data"` 等 3.12+ 特性）
- 排除 `__pycache__`、`*.pyc`、`.DS_Store`
- 导入时保留原始目录结构

## 对标 OpenWork

OpenWork 核心模式：Skills 配置一次 → 打包分享 → 一键导入。skill-porter 实现本地等价物。叠加 `quick-tunnel-deploy` 可实现公网分享链接。

## 陷阱

- Python < 3.10 必须用 `Optional[Path]` / `Optional[str]`，不能用 `Path | None`
- `tarfile.extractall(filter="data")` 是 Python 3.12+ 特性，不能用
- `.archive` 和 `.disabled_archive` 目录下的旧版本 skills 也会被列出
- 导入时如目标已存在且未传 `-f`，会报错退出
