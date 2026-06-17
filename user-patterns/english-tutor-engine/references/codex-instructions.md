# Codex 介入指令 — 英语伴学引擎 v2.0

## 📍 项目定位

考研英语 AI 伴学系统，运行在 Hermes Agent 的 `english-tutor` profile 下。
所有代码在本地，通过 GitHub 同步。

## 📁 关键路径

```
/Users/mac/.hermes/profiles/english-tutor/
├── bin/                          # 核心脚本（主仓库）
│   ├── vocab_lib.py              # ⭐ 共享库 — 所有脚本的依赖
│   ├── engine_upgrade_sample_descent.py  # 升级判定 + 抽样 + 降级
│   ├── phase2_sentence_understanding.py  # 阶段2：句子理解
│   ├── daily_feedback.py         # 每日反馈 + 进度环
│   ├── fast_vocab_round.py       # Phase1：闪卡出题
│   ├── reset_rank.py             # 段位重置工具
│   └── learning_path.py          # 学习路径引擎
├── tests/                        # 单元测试
│   └── test_vocab_lib.py         # vocab_lib 的 pytest 测试
├── state/                        # 运行时状态
│   └── gamification.json         # 段位/XP/进度
└── home/.hermes/repos/data/      # GitHub 镜像仓库
    ├── words.json                # ⭐ 词库主表（1341条，list of dict）
    ├── rank_config.json          # 升级规则配置
    ├── _quiz.json                # 抽样测试结果
    ├── _phase2_sentences.json    # 阶段2题目
    ├── scripts/                  # 脚本副本（与 bin/ 同步）
    └── tests/                    # 测试副本
```

## 🔑 数据契约（必须遵守）

### words.json 结构
```json
{
  "words": [
    {
      "word": "abstract",
      "phonetic": "/æbˈstrækt/",
      "meaning": "抽象的；摘要",
      "is_core": true,
      "core_level": 1,
      "source": "anki_import",
      "mastery": 75,           // ⚠️ 范围 0-100，不是 0-1
      "review_count": 4,
      "correct_count": 3,
      "error_types": [],
      "history": [...]
    }
  ],
  "meta": {"total": 1341, "core_count": 1338, "last_updated": "..."}
}
```

### gamification.json 结构
```json
{
  "rank": "青铜",              // 青铜/白银/黄金/铂金/钻石/王者
  "sub_rank": "I",             // ⚠️ 只存罗马数字 I/II/III/IV，不要带 rank 前缀
  "rank_progress": 0.0,
  "xp": 0,
  "phases": {
    "phase2": {"activated": true, "mode": "sentence_fill_blank"},
    "phase3": {"activated": false},
    "phase4": {"activated": false}
  }
}
```

### 核心规则
1. **mastery 范围是 0-100**，不是 0-1。所有比较都用 >= 50 表示半掌握。
2. **sub_rank 只存罗马数字**（I/II/III/IV），显示时拼上 rank 前缀。禁止写 `铂金铂金I`。
3. **覆盖率分母 = 核心词数**（1338），不是总词数。
4. 所有修改必须通过 `bin/vocab_lib.py` 的共享函数，不要在各脚本里重复实现指标计算。

## 🏗️ 架构原则

### 依赖关系
```
fast_vocab_round.py ──┐
engine_upgrade_...py ─┼──→ vocab_lib.py（共享库，唯一数据访问层）
phase2_sentence...py ─┤
daily_feedback.py ─────┘
learning_path.py ──────┘
```

### 修改流程
1. **先读 `bin/vocab_lib.py`** — 了解现有 API，不要重写
2. **新增功能 → 加到 vocab_lib.py**，不要在各脚本里重复
3. **修改现有函数签名 → 检查所有调用方**，确保兼容
4. **写测试 → `tests/test_vocab_lib.py`**，必须 `pytest` 全通过
5. **同步到 GitHub → `home/.hermes/repos/data/`**

### 绝对禁止
- ❌ 直接在 `words.json` 里写硬编码的数字（如 1328）
- ❌ 在 vocab_lib.py 之外实现 `get_current_stats()` 逻辑
- ❌ 修改 `rank_config.json` 的结构（六段位+子段位是固定的）
- ❌ 破坏 `student_matches()` 的判分逻辑（已支持精确/包含/关键词重叠50%）

## 📋 当前任务清单

### 已完成 ✅
- [x] 50个作文万能句型入库（words.json +47条）
- [x] 升级规则重构（rank_config.json 六段位多维达标）
- [x] 段位重置（修复刷段 bug，铂金I→青铜I）
- [x] 每日存量反馈（三环进度环）
- [x] 抽样测试 + 降级机制
- [x] vocab_lib.py 共享库
- [x] 14 个 pytest 全通过
- [x] 学习路径引擎（盲区分析 + 周计划）

### 待优化 🔧
1. **抽样语义判分升级**：当前关键词匹配太粗糙，改用 LLM 做语义相似度
2. **降级报告可视化**：生成 HTML 报告推 Telegram
3. **阶段2填空参考答案**：50个句型需要英文参考+中文释义

## 🤝 协作方式

### 启动命令
```bash
cd /Users/mac/.hermes/profiles/english-tutor && python3 ~/aider_workspace/bridge_cmd.py "任务描述"
```

### 给 Codex 的提示词模板
```
你是一个 Python 工程师，正在修改 /Users/mac/.hermes/profiles/english-tutor/ 下的英语伴学引擎。

必读文件：
1. /Users/mac/.hermes/profiles/english-tutor/CODEX_INSTRUCTIONS.md — 项目架构和数据契约
2. /Users/mac/.hermes/profiles/english-tutor/bin/vocab_lib.py — 共享库（不要重写，只扩展）
3. /Users/mac/.hermes/profiles/english-tutor/bin/engine_upgrade_sample_descent.py — 主引擎
4. /Users/mac/.hermes/profiles/english-tutor/home/.hermes/repos/data/words.json — 词库

任务：[具体任务描述]

要求：
- 修改前必须先读 vocab_lib.py，了解现有 API
- 新增功能加到 vocab_lib.py，不要在各脚本里重复
- 修改函数签名前，grep 所有调用方确保兼容
- 写 pytest 测试，确保 100% 通过
- 修改后运行 python3 -m pytest tests/ 验证
```

### 验证步骤（Codex 完成后必须执行）
```bash
cd /Users/mac/.hermes/profiles/english-tutor
python3 -m pytest tests/ -v          # 所有测试通过
python3 bin/engine_upgrade_sample_descent.py  # 引擎正常运行
python3 bin/daily_feedback.py        # 反馈正常输出
git -C home/.hermes/repos/data add -A && git -C home/.hermes/repos/data commit -m "..." && git -C home/.hermes/repos/data push
```

## 📊 当前系统状态快照
- 总词数：1341
- 核心词：1338
- 已练习：127
- 覆盖率：9.5%
- 平均掌握度：3.2%
- 当前段位：青铜I
- 阶段2：已激活（句子填空）
- 阶段3：未激活（覆盖率<50%）
- 阶段4：未激活（覆盖率<80%）
