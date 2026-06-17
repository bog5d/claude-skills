# vocab_lib 共享库架构（2026-06-17 更新）

## 定位

`bin/vocab_lib.py`（930行）是英语伴学引擎的统一数据层和业务逻辑层。所有 CLI 脚本通过 `import vocab_lib as vl` 引用。

**铁律**：任何脚本不得在 vocab_lib.py 之外实现 `get_current_stats()`、`build_learning_profile()`、`build_feedback_prescription()` 等核心指标计算。

## 核心 API

### 数据加载
- `load_json(path)` — 安全加载 JSON，不存在返回 {}
- `save_json(path, data)` — 安全保存 JSON，自动创建目录
- `load_words()` → list — 加载词库（1341条，兼容无参和显式路径）
- `load_gamification()` → dict — 加载 gamification 数据
- `load_rank_config()` → dict — 加载升级规则
- `load_study_plan(path)` → dict — 加载学习路径
- `save_study_plan(plan, path)` → 保存学习路径

### 指标计算
- `get_current_stats(words)` → dict:
  - `coverage_pct`: 覆盖率 0-100
  - `mastery_avg`: 平均掌握度 0-100（全局，分母=核心词总数）
  - `practiced_mastery_avg`: 已练词平均掌握度 0-100（分母=已练词数）
  - `error_clear`: 错题攻克数（mastery >= 50 且有 error_types）
  - `core_count`: 核心词总数
  - `reviewed_count`: 已练习数
  - `source_stats`: 来源分组统计

### 五维学习画像
- `build_learning_profile(words)` → dict:
  - `recognition`: 识别能力（已练词数 / 核心词数 × 100）
  - `recall`: 回忆能力（已练词平均 mastery）
  - `context`: 语境能力（有 history 记录的词占比）
  - `output`: 输出能力（diary 来源词占比）
  - `stability`: 稳定性（mastery >= 50 且 interval >= 3 的词占比）

### 学习处方
- `build_feedback_prescription(words, gam_data, rank_config, plan)` → dict:
  - `rank_display`: 段位显示（青铜I，非铂金铂金I）
  - `stats`: 覆盖率/全局掌握/已练掌握
  - `progress_to_next`: 距下一段位进度百分比
  - `today_plan`: 今日任务（词数、时间、重点、前8词）
  - `actions`: 升级行动指引列表
  - `learning_profile`: 五维画像

### StudyPlan schema
- `build_study_plan(words, days=7, daily_limit=20)` → dict:
  - `schema_version`: 1
  - `overview`: coverage_pct / mastery_avg / reviewed_count / core_count
  - `today_plan`: day/date/words/items/sources/target.focus
  - `weekly_plan`: 7天计划列表
  - `top_priorities`: 前50优先级词
  - `word_priority`: 前200词的 priority map（供 fast_vocab_round 引用）

### 段位判定
- `get_current_rank(gam_data, rank_config)` → (rank: str, sub: str)
- `check_can_upgrade(words, gam_data, rank_config)` → (bool, reason: str, next_rank_name: str)
- `check_rank(stats, gam_data, rank_config)` → dict（含 progress_to_next + checks）
- `get_progress_to_next(words, gam_data, rank_config)` → (progress: float, checks: list)

### 抽样测试
- `run_sample_test(words, sample_size=30)` → (questions, error)
- `grade_sample_test(submitted_answers, questions)` → 结果 dict（含 accuracy/blind_spots/recommendations）

### 判分逻辑
- `student_matches(student_ans, correct_ans)` → bool — 精确/包含/关键词重叠≥50%
- `grade_answer_semantic(student_ans, correct_ans, word)` → dict:
  - `score`: 0-100
  - `is_correct`: bool
  - `method`: 'deterministic' | 'local_semantic' | 'empty'
  - `matched_meaning`: 匹配到的义项
  - `missing_meaning`: 漏掉的义项
  - `error_type`: 错误类型（记忆空白/释义偏差/未作答）
  - `feedback`: 可解释反馈

### 降级检测
- `check_descent(words, gam_data, rank_config)` → (needs_descent, report, gam_data)

### 阶段激活
- `check_phase_activation(stats, gam_data)` → (message, gam_data)

## 别名兼容层（多 Agent 协作产物）

以下别名确保 Codex 重构的 engine/phase2 仍能正常工作（见 pitfall 36）：

```python
# 安全文件操作别名
load_json_safe = load_json
save_json_safe = save_json

# 指标计算别名（签名适配）
calc_coverage = lambda words, core_count: ...
calc_mastery_avg = lambda words, core_words: ...
calc_error_clear = lambda words: ...

# 段位工具函数
extract_sub_num(raw: str) → str — 从 '铂金IV' 提取 'IV'
format_rank(rank: str, sub: str) → str — 避免重复前缀
check_rank(stats, gam_data, rank_config) → dict — 含进度信息

# 判分别名
student_match = student_matches  # 单数→复数

# 升级判定适配（参数顺序适配）
check_can_upgrade_compat(stats, rank_config, gam_data) → tuple
check_can_upgrade = check_can_upgrade_compat
```

## 数据契约

- **mastery**: 0-100 整数刻度（非 0-1 浮点）
- **sub_rank**: 罗马数字 I/II/III/IV（不带 rank 前缀）
- **words.json**: `{"words": [...list of dict...], "meta": {...}}`
- **核心词判断**: `w.get('is_core')` 为 True
- **覆盖率分母**: 核心词数（1338），不是总词数

## 单元测试

`tests/test_vocab_lib.py` — 14 tests, 覆盖：
- 判分逻辑（精确/包含/关键词重叠/无匹配）
- 指标计算（覆盖率/掌握度/错题攻克/非核心排除）
- 抽样测试（判分/生成/不足5词）
- 进度计算

`tests/test_vocab_contracts.py` — 9 tests, 覆盖：
- 数据契约（mastery 0-100、sub_rank IV、覆盖率分母）
- StudyPlan schema 结构
- Phase2 迁移训练校验
- 结构化语义判分

## 与多 Agent 协作注意事项

当多 Agent 修改同一批文件时（2026-06-17 真实事故教训）：
1. 先在 vocab_lib.py 中注册新函数名
2. 其他脚本引用已注册函数名，不自行发明
3. 参数签名必须一致（参考上方 API 列表）
4. 每次合并后跑 `pytest tests/test_vocab_lib.py -v` 验证
5. 跑 `python3 bin/engine_upgrade_sample_descent.py` 验证引擎正常
6. 跑 `python3 bin/daily_feedback.py` 验证反馈输出正常

## Pipeline 整合（2026-06-17 确立）

**核心原则**：所有独立脚本必须汇入一条 pipeline，不能各跑各的。

```
learning_path.py → 优先级推荐词
    ↓
fast_vocab_round.py → 出题（受优先级引导，diary优先）
    ↓
session_pipeline.py → 判分 + SM-2 + 五层讲解 + gamification
    ↓
engine_upgrade_sample_descent.py → 升级/降级/抽样检测
    ↓
daily_feedback.py → 今日学习处方（三环进度环 + 五维画像）
    ↓
learning_path.json → 回灌学习路径（数据闭环）
```

`fast_vocab_round.py` 的 `select_words()` 通过 `_load_plan_priority()` 读取 `word_priority` map，优先选取高优先级词。`daily_feedback.py` 通过 `build_feedback_prescription()` 把状态翻译成今日行动。
