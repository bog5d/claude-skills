# vocab_lib 共享库架构（2026-06-17 确立）

## 定位

`bin/vocab_lib.py` 是英语伴学引擎的统一数据层和业务逻辑层。所有 CLI 脚本通过 `import vocab_lib as vl` 引用。

## 核心 API

### 数据加载
- `load_json(path)` — 安全加载 JSON，不存在返回 {}
- `save_json(path, data)` — 安全保存 JSON，自动创建目录
- `load_words()` → list — 加载词库
- `load_gamification()` → dict — 加载 gamification 数据
- `load_rank_config()` → dict — 加载升级规则

### 指标计算
- `get_current_stats(words)` → dict:
  - `coverage_pct`: 覆盖率 0-100
  - `mastery_avg`: 平均掌握度 0-100
  - `error_clear`: 错题攻克数
  - `core_count`: 核心词总数
  - `reviewed_count`: 已练习数
  - `source_stats`: 来源分组统计

### 段位判定
- `get_current_rank(gam_data)` → (rank: str, sub: str)
- `check_can_upgrade(stats, rank_config, gam_data)` → (bool, reason: str, next_rank_name: str)
- `get_progress_to_next(words, gam_data, rank_config)` → (progress: float, checks: list)

### 抽样测试
- `run_sample_test(words, sample_size=30)` → (questions, error)
- `grade_sample_test(submitted_answers, questions)` → 结果 dict（含 accuracy/blind_spots/recommendations）

### 判分逻辑
- `student_matches(student_ans, correct_ans)` → bool — 精确/包含/关键词重叠≥50%

### 降级检测
- `check_descent(words, gam_data, rank_config)` → (needs_descent, report, gam_data)

### 阶段激活
- `check_phase_activation(stats, gam_data)` → (message, gam_data)

## 别名兼容层（pitfall 36 产物）

以下别名确保 Codex 重构的 engine/phase2 仍能正常工作：

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

## 单元测试

`tests/test_vocab_lib.py` — 14 tests, 覆盖：
- 判分逻辑（精确/包含/关键词重叠/无匹配）
- 指标计算（覆盖率/掌握度/错题攻克/非核心排除）
- 抽样测试（判分/生成/不足5词）
- 进度计算

## 与多 Agent 协作注意事项

当多 Agent 修改同一批文件时（2026-06-17 真实事故教训）：
1. 先在 vocab_lib.py 中注册新函数名
2. 其他脚本引用已注册函数名，不自行发明
3. 参数签名必须一致（参考上方 API 列表）
4. 每次合并后跑 `pytest tests/test_vocab_lib.py -v` 验证
5. 跑 `python3 bin/engine_upgrade_sample_descent.py` 验证引擎正常
