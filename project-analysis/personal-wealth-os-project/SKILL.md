---
name: personal-wealth-os-project
description: 维护 personal-wealth-os 代码库（TDD、run.py 自动提交、数据耦合测试）。
---

# Personal Wealth OS 项目卡

## When to Use
- 任务涉及 /Users/mac/personal-wealth-os 的改代码、修 Bug、跑测试、跑 run.py、push
- 波总提到"财富纪律系统""wealth-os""个人财富 OS"的代码层面工作

> 通用 git 操作坑（脚本自动 add -A、commit message 中文标点触发安全扫描）见
> `references/git-commit-pitfalls.md`。

## 仓库
- 路径 `/Users/mac/personal-wealth-os`；remote origin = https://github.com/bog5d/personal-wealth-os.git（credential helper 已配置，push 直接可用）
- **Python 3.9 兼容**：禁止 3.10+ 语法（match / dict `|` 合并等）
- 依赖仅标准库 + PyYAML

## 结构
- `engine/{normalize,validate,portfolio_engine,strategy_engine,risk_engine,report}.py`
- `run.py` 一键闭环：inbox → normalize → validation → **apply** → build_snapshot → strategy → risk → daily/weekly 报告 → audit jsonl → **git 自动提交**
- 数据流：`data/inbox/*.yaml`（六字段 date/asset_id/field/value/source/confidence）→ `data/normalized/latest.json`
- `portfolio/`：`assets.yaml`（静态身份）、`strategy_mapping.yaml`、`current_snapshot.yaml`（动态状态，load_portfolio 合并进 assets 视图）
- `tests/`：106 例全绿（v0.1.1 基线 2026-08-27）

## 开发铁律（波总定的）
1. **TDD**：先写测试看红，再改代码看绿
2. **git add 具体文件**，禁止 `git add -A`
3. push 前 `git fetch` 检查远端新提交；远端领先先 rebase 再动代码

## ⚠️ 最大坑：run.py 末尾自动 `git add -A` + commit
每次运行自动执行 `git add -A && git commit -m "auto: wealth-os run <date>"`。
→ **改完代码必须先 commit 自己的文件，再跑 run.py**，否则改动被扫进 auto commit。
auto commit 应只含运行产物（current_snapshot.yaml / reports/ / audit/ / data/history/）。
另：每次 run.py 都追加 audit jsonl → 每次运行产生一个新 auto commit，属正常现象。

## ⚠️ 数据耦合测试
`tests/test_portfolio.py` 直接断言 `current_snapshot.yaml` 的精确求和（总资产 / 六桶小计 / stale 资产清单）。
任何会改变快照数据的修复，提交顺序必须保证**每个 commit 时点套件全绿**：
1. commit A：修复代码 + 新测试（此时旧期望值仍匹配旧数据 → 绿）
2. 跑 `python3 run.py` 应用新数据（auto commit B 收走产物）
3. commit C：单独更新 test_portfolio.py 期望值 → 绿
4. 全套 `python3 -m pytest tests/ -q` 确认 → push

## v0.1.1 修复记录（2026-08-27）
- 缺陷：normalized 的 `field=current_value` 从未写回快照 → current_snapshot.yaml / 聚合 / 周报沿用旧值（fund_007751=646.29，PE_TRAFFIC_LIGHT=3869.39 是旧值之和）
- 修复：`engine/portfolio_engine.apply_normalized_updates(snapshot, assets, normalized)`，run.py 在 run_validation 之后、build_snapshot 之前调用；同步更新 snapshot.assets[id] 与 merged assets 视图的 current_value/last_updated(record.date)/data_source(record.source)/confidence(record.confidence)；非法 asset_id（含 PE_PERCENTILE 元数据）与非数值 value 一律忽略
- PE_PERCENTILE 既有提取逻辑（run.py 150-155 行）未动
- 修复后值：fund_007751=2843.78、fund_519671=2309.39、fund_002963=2755.22、bond_yinhua_usd=97.46；总资产 15580.85；PE_TRAFFIC_LIGHT=7343.34
- 测试：`tests/test_apply_normalized_updates.py` 6 例（应用+四字段 / 写盘聚合 / 非法 id / 元数据 / 非 current_value / 非数值）——注意断言不得硬编码 live 快照旧值，先取 before 再比 after，保证与运行顺序无关

## 已知事项
- `PE_PERCENTILE` 是元数据资产（validate.py `META_ASSET_IDS`），不在资产注册表
- snapshot_date 2026-01-17 为考古时点 → 系统诚实报 STALE，直到 inbox 放最新截图数据
- mmf_jiashi current_value=null（价值未知）；fund_guotianhui UNCLASSIFIED 待用户确认归属
- crypto_btc/eth 停在 2025-11-07 → 仍属 stale_assets（断言用 crypto_btc）
