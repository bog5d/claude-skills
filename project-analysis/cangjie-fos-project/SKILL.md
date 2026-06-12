---
name: cangjie-fos-project
description: 仓颉 FOS（融资作战系统）项目环境速查卡。克隆、依赖、测试、已知问题、多AI并行协议、当前待办。
category: project-analysis
---

# 仓颉 FOS 项目速查卡

## Sub-Skill Map

| Workflow | Reference |
|----------|-----------|
| Structured project analysis | `references/fos-project-analysis-workflow.md` |
| Screenshot capture for manuals | `references/fos-screenshot-capture.md` |
| Public deployment via SSH tunnel | `references/fos-public-deploy.md` |

## 接手第一步
```bash
git clone https://github.com/bog5d/cangjie-fos.git
cd cangjie-fos/backend
uv sync --extra dev
uv run --extra dev pytest tests/ --ignore=tests/test_doctor_script.py -q
# 应看到：605 passed，0 failed
```

## 项目结构
```
cangjie-fos/
  backend/src/cangjie_fos/     ← FastAPI + SQLite + LangGraph（124 py文件）
  backend/src/cangjie_fos/engine/  ← 分析引擎（已内置，v0.5.5 后无外部依赖）
  backend/tests/               ← 60 测试文件
  frontend/src/                ← React + TypeScript + Vite（56 tsx/ts 文件）
```

## 开发铁律（TDD 工作流）

### 每次修 Bug / 加功能必执行
1. **分析根因**：读相关代码 → 找到确切行号
2. **先写测试（红）**：创建/扩展测试文件，覆盖正常流 + 边界 + Bug 场景
3. **跑测试确认失败**：`pytest tests/test_xxx.py -v` — 必须看到失败
4. **修复代码（绿）**：最小改动，不改无关逻辑
5. **跑测试确认通过**：`pytest tests/test_xxx.py -v` — 全部通过
6. **跑全套确认回归**：`pytest tests/ --ignore=tests/test_doctor_script.py -q`
7. **更新文档**：CHANGELOG.md + AGENTS.md（版本号、测试基线、Bug状态）
8. **提交**：`git add <具体文件>` → commit → push

### 禁止行为
- ❌ 改完说"应该好了你试试" → 必须先跑测试证明
- ❌ `git add -A` → 可能提交 .env
- ❌ push 前不 git fetch → 多 AI 并行会冲突
- ❌ 新增 API 不写测试

## 关键架构约定

| 约定 | 说明 |
|------|------|
| `pitch_jobs.institution_id` | 存**机构名字符串**，不是 UUID |
| Review API 数据源 | 只读 SQLite（`db_job_get`），不读内存 |
| Pipeline 写入 | 必须同时写内存（`job_update`）+ SQLite（`db_job_update`） |
| 字段名权威来源 | `engine/schema.py`，前端 TS 接口必须对齐 |
| `key_verbatim_moments` | `List[str]`，不是对象列表 |
| 缺包 | `uv add <package>`，不用 pip |

## 当前状态（v0.6.8，2026-05-15）

| 项目 | 状态 |
|------|------|
| 版本 | **v0.6.8** |
| 测试基线 | **605 passed**，0 failed，0 skipped |
| CHANGELOG | ✅ v0.6.6/0.6.7/0.6.8 已补录 |
| 13个同事反馈 | **13/13 全部已修复** ✅ |

### v0.6.8 关键架构变更
- `get_audio_dir()` 统一音频路径（`CANGJIE_AUDIO_DIR` 环境变量覆盖）
- `_isolate_db_per_test` autouse：每测试独立 SQLite
- `@pytest.mark.real_db` marker 自声明（替代中央豁免列表）
- `.git/hooks/pre-push` 自动跑 DB fixture 测试
- 10 个 bare `except Exception` 收敛为具体异常类型

### 下一版接手方向
- llm_judge 1763 行巨兽拆分为子模块
- 36 个裸 except 继续收敛
- Docker 部署

## 测试架构约定（v0.6.8 新增）

### DB 隔离：`_isolate_db_per_test` + `@pytest.mark.real_db`

- `conftest.py` 的 `_isolate_db_per_test` fixture（autouse, function scope）为每测试创建独立 SQLite 临时库
- **测试文件若用 module/class 级 fixture 预写 DB 数据，必须加 `pytestmark = [pytest.mark.real_db]`** 声明豁免
- Marker 已在 `pyproject.toml` 注册，fixture 通过 `request.node.get_closest_marker("real_db")` 检测
- 已标记文件：`test_wizard_pipeline_e2e`, `test_pipeline_e2e`, `test_p0_retry_eval`, `test_follow_ups_api`, `test_wiki_display`
- `.git/hooks/pre-push` 自动跑上述 5 个文件，防止 scope mismatch 打红
- **新增 module-fixture 测试文件必须加 `pytestmark`**，否则会读到空 DB 全线失败

### Mock 级 E2E 测试模式

- Wizard/Pipeline E2E 用 `module` scope fixture 跑一次 pipeline（mock ASR + LLM）
- 各 test 验证 DB 落盘 + Review API 返回，不依赖真实外部服务
- 内存 job store 和 SQLite 双写已 mock 为同步

## 已知代码问题

| 问题 | 严重度 |
|------|--------|
| `llm_judge.py` 1763行巨兽需拆分 | 🔴 高 |
| 36 个裸 `except Exception`（v0.6.5 时 61→v0.6.8 降至 36） | 🟡 中 |
| `dashboard.py`/`war_room.py` 各出现在两个目录 | 🟡 中 |
| 约40%后端模块缺专属测试 | 🟡 中 |

### Bare except 收敛策略

- **回调函数** → `except Exception as e:` + `logger.warning/exception`（仍宽广，但不静默）
- **内部可控函数** → 窄化到具体异常类型（`RuntimeError, ValueError, json.JSONDecodeError...`）
- 扫描命令：`grep -rn "except Exception" backend/src/cangjie_fos/ | grep -v "# noqa"`

## 多 AI 并行开发协议

1. 每次改代码前：`git fetch origin master` → 用 `git-precheck` 技能检查三方向
2. 远端有新 commit：`git stash && git pull --rebase origin master && git stash pop`
3. CHANGELOG 版本冲突：远端版本保留，本地版本 bump +1（如 0.6.1 → 0.6.2）
4. Push 前确认 AGENTS.md 版本号不重复
5. macOS Push 认证：用 credential helper 内联方式（见 git-precheck 技能）。**注意**：临时 clone（/tmp 下）credential helper 可能挂死无输出，改用 token-in-URL：`git push https://<PAT>@github.com/bog5d/cangjie-fos.git master`
