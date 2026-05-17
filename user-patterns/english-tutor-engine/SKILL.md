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

## 估分公式

```
est = 25 + (coverage_pct/100 × 0.4 + avg_mastery × 0.6) × 75
```

## Anki 导入流水线

1. **解析**：手动 tab-split（不用 csv.reader，引号会炸），跳过 `#` 开头行
2. **分类**：跳过中文开头卡片（`（真题原句`）和语法卡片（含 `Kaoyan Syntax`/`同位语`/`公式`）
3. **提取单词**：regex `^([a-zA-Z][a-zA-Z\s\-/()]+?)(?:\s*(?:/\S+?/)?\s*(?:Kaoyan|考研|<br>|$))`
4. **去重**：统一 lower → 与现有 words.json 比对
5. **写入**：words.json + progress.json → git push

## 铁律

- 词库最终格式统一小写
- GitHub 是单一事实源，每次数据变更立即 git push
- 不主动处理副官/融资/企业治理任务 — 英语专属
- 单词释义每题必带音标；词根词源拆解采用「前缀+词根+后缀+演化链」格式
- Grillme 访谈在 Telegram 用 A/B/C/D/E 内联选项代替 clarify 工具
- 表格/对比/多维度数据生成截图图片发送，不用 Markdown 源码
- PPT = PPT Master .pptx (亮色/白底专业风)，不用暗黑主题
