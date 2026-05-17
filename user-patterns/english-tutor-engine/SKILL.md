---
name: english-tutor-engine
description: 考研英语 AI 伴学引擎。SM-2 间隔重复词库 + 5 模式闪卡测试 + 词汇量追踪 + 游戏化闯关。当波总要求英语测试、问进度或讨论英语学习体系时使用。
category: user-patterns
trigger:
  - 英语单词
  - 背单词
  - 词汇测试
  - 英语学习
  - 考研英语
  - 闪卡 / flashcard
  - 来一局 / 闯关
  - 进度 / 段位 / 估分
  - 导入Anki / 导出Anki
---

# English Tutor Engine — 考研英语 AI 伴学引擎

## 架构

```
波总 ↔ Hermes (Telegram 对话)
         ↓
  GitHub: bog5d/bog-vocab-tracker (私有仓库)
  ├── data/words.json        (词库主表, 1331 词 / 1328 核心)
  ├── data/progress.json     (进度/段位/积分/里程碑)
  ├── data/sessions.json     (学习会话记录)
  ├── data/config.json       (游戏规则 + 模式 + 能力树 + 宝箱)
  ├── data/anki_export/      (回导 Anki CSV 存档)
  └── scripts/
      ├── game_master.py     (多模式闯关引擎)
      ├── sm2_engine.py      (SM-2 选题 + 更新)
      └── anki_bridge.py     (Anki 双向导入/导出)
```

## 六件事（按出现频率）

### 1. 开一局闯关 — 最高频

用户说「来一局」/「开战」/「测试」→ `game_master.pick_quiz_pool(5, "review")`
- SM-2 到期词优先 → 错题优先 → 未练词补位
- 从 `words.json` 的 `next_review` 字段筛选
- 每题答完调用 `game_master.apply_answer()` 更新 SM-2 状态

### 2. 多模式切换

模式一览（配置在 `config.json.game_modes`）：

| 模式 | 对应技能 | 触发方法 |
|------|---------|---------|
| `review` | 阅读理解 (EN→CN) | 默认「来一局」 |
| `reverse` | 写作翻译 (CN→EN) | 「反向测试」 |
| `synonym` | 同义词辨析 | 「来个同义词」 |
| `listen` | 听力理解 | 「测个听力」（配合 text_to_speech） |
| `spell` | 拼写测试 | 👷 待实现 |

调用：`game_master.gen_quiz(word, mode="synonym", all_words=...)`

### 3. 查进度 / 段位 / 估分

「当前状态」→ `game_master.calc_prediction()` 返回：
- coverage_pct, avg_mastery, estimated_score, rank, days_to_65

段位表（config.json.ranks）：
青铜 → 白银(10%/30%) → 黄金(25%/45%) → 铂金(40%/55%) → 钻石(60%/70%) → 王者(80%/85%) → 考研战神(100%/90%)

### 4. 词根能力树

「能力树」/「词根」→ `game_master.gen_skill_tree_panel()`
10 个词根家族：-tend, -spect, -mit, -pose, -dict, -duce, -cess, -tain, -form, -port
每个家族统计：unlocked / total + avg_mastery%

### 5. Anki 双向桥

**导入：** 用户传 Anki txt → `anki_bridge.import_anki_txt(path)`
- 自动解析 tab-separated，跳过语法卡
- 提取单词 + 中文释义
- 增量合并到 `words.json`
- 核心词自动标记 is_core=True

**导出：** 「导出Anki」→ `anki_bridge.export_anki_csv(path)`
- 字段：Word / Phonetic / Meaning / Mastery / NextReview / ErrorTypes

### 6. 连击宝箱

config.json.streak_chest 定义：
- 连击 3/5/7/10 → 额外 +5/15/25/50 分
- 3 连中触发 bonus round（超纲词，答对 +30，不答不扣）

## 数据字段 (words.json 每词)

```json
{
  "word": "abstract",
  "phonetic": "/ˈæbstrækt/",
  "meaning": "抽象的；摘要",
  "is_core": true,
  "core_level": 1,
  "source": "anki_import" | "preset_1500",
  "mastery": 0.0,
  "review_count": 0,
  "correct_count": 0,
  "error_types": ["近义混淆"],
  "ef": 2.5,
  "interval": 1,
  "next_review": "2026-05-17",
  "last_reviewed": null,
  "first_seen": "2026-05-17"
}
```

## SM-2 公式

```
答对 → ef += 0.1, interval = int(interval × ef), next_review = today + interval
答错 → ef -= 0.2 (min 1.3), interval = 1, next_review = tomorrow
```

## 分阶段多维预测模型 (config.json.prediction.multi_phase)

### Phase 1 (当前 — 覆盖率<30% 或 掌握率<40%)
- 输出：词汇预测分
- 公式：`25 + (覆盖率×0.4 + 掌握率×0.6) × 75`
- 标注：`score_type: "词汇预测分"`（告知只反映词汇基础，不含阅读/翻译/写作）
- 设计依据：Nation 2006 98%覆盖率理论（<80%前阅读分极低）

### Phase 2 (解锁条件：覆盖率≥30% 且 掌握率≥40%)
- 增加：阅读分 = `掌握率 × 覆盖率因子 × 40`
- 输出：词汇分 + 阅读分
- 设计依据：Laufer 1992 词族研究 + Qian 2002 词汇深度理论

### Phase 3 (解锁条件：覆盖率≥50% 且 掌握率≥55%)
- 增加：翻译分 = `掌握率 × 15`，写作分 = `掌握率 × 25`
- 输出：完整四维分表（词汇+阅读+翻译+写作）
- 设计依据：Schmitt 2010 刻意学习路径

### 达标预测
- 需要 ≥10 词复习记录才激活
- 早期：用已复习词均值（不稀释到全量 1328 词）
- 速率：`avg_m × 0.10` 为每 session 掌握率增幅
- 输出 `days_to_65` 和 `target_date_65`

## Anki 导入流水线

1. **解析**：手动 tab-split（不用 csv.reader，引号会炸），跳过 `#` 开头行
2. **分类**：跳过中文开头卡片（`（真题原句`）和语法卡片（含 `Kaoyan Syntax`/`同位语`/`公式`）
3. **提取单词**：regex `^([a-zA-Z][a-zA-Z\s\-/()]+?)(?:\s*(?:/\S+?/)?\s*(?:Kaoyan|考研|<br>|$))`
4. **去重**：统一 lower → 与现有 words.json 比对
5. **写入**：words.json + progress.json → git push

## ⭐ 单词讲解协议（每词必遵守）

每词回答后按 5 层格式输出，不允许省略任何层：

```
## 🔬 [单词] — 拆解

[1. 词根拆解：前缀+词根+后缀，标注来源语，列2-3同源词]
[2. 演化链：拉丁→古法→现代英语，字面含义推导]
[3. 视觉锚点：一句画面感描述（荒谬>现实，个人化>通用化）]
[4. 原卡时空背景：从Anki导入的原始卡片内容——时空坐标+波总原声+地道纠偏]
[5. 考研语境锚：Lv1-2词标注真题出处]
```

## 🧠 全球记忆大师工具箱

| 技巧 | 方法 | 示例 |
|------|------|------|
| 词根映射 | 用已知推未知 | lever 已知 → alleviate (共享 levi=轻) |
| 对立面映射 | 同一词根正反同时讲 | attract vs distract vs extract |
| 触觉锚点 | 身体感受代替抽象理解 | abstract = 伸手把实物抽走 |
| 时间线叙事 | 放入用户真实时间线 | 「4月8日你在高铁上同时学了 aisle/passenger/monitor」 |
| 词根族点亮 | 答对3词 → 标记族已解锁 | -tract 族 3/6 已点亮 |

## 错题记录要求（升级）

不仅存 `error_types` 标签，必须存每次错误的**用户完整回答原话**到 `sessions.json → error_log`：
```json
{"timestamp":"...", "word":"abstract", "user_response":"是形容词还是动词？想不起来", "correct_answer":"抽象的；摘要", "error_type":"记忆模糊"}
```

## 新增 A/B/C/D 系统

### A: 词根族点亮
- 每词带 `root_family` 字段（10个根族）
- 当同一根族 mastery≥0.5 词数 ≥ 半时 → 标记解锁

### B: 连击宝箱 2.0
- 连击触发时抽超纲词（15个词池）→ 答对+30分 + 存入「我的收藏」
- 答错不扣分

### C: 考研场景沉浸
- 80个Lv1词标真题出处（config.json.exam_anchors）
- 每5关触发迷你真题阅读生成

### D: 知识晶体导出
- `scripts/wordcloud_gen.py` — HTML词云 + 音标速查表
- 每掌握50词自动建议生成

## 全量设计文档（仓库内）

- `EXPERT_SYSTEM.md` — AI 接手第一读本（完整协议）
- `docs/WORD_TEMPLATE.md` — 单词讲解模板 + 全球记忆大师工具箱
- `docs/GAME_DESIGN.md` — 游戏化设计依据（Octalysis/SDT/Flow）+ 优化路线图
- 换 AI 只需：clone → 读 EXPERT_SYSTEM.md → 继续闯关

## 铁律

- 词库最终格式统一小写
- GitHub 是单一事实源，每次数据变更立即 git push
- 不主动处理副官/融资/企业治理任务 — 英语专属
- 每词必发音标；讲解必走5层协议；原卡时空背景不能省略
- Grillme 访谈在 Telegram 用 A/B/C/D/E 内联选项代替 clarify 工具
- 新 AI 接手先读 EXPERT_SYSTEM.md（包含完整协议）
- 表格/对比/多维度数据生成截图图片发送，不用 Markdown 源码
- PPT = PPT Master .pptx (亮色/白底专业风)，不用暗黑主题
