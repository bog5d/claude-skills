---
name: english-tutor-engine
description: 考研英语 AI 伴学引擎。SM-2 间隔重复词库 + 闪卡测试 + 词汇量追踪。当波总在 @Engcjd_bot 发送英语单词或要求英语测试时使用。
category: user-patterns
trigger:
  - 英语单词
  - 背单词
  - 词汇测试
  - 英语学习
  - 考研英语
  - 闪卡
  - flashcard
---

# English Tutor Engine — 考研英语 AI 伴学引擎

## 两套系统

| 系统 | 存储 | 入口 | 适用 |
|------|------|------|------|
| **Hermes 对话引擎** (本 skill 主) | GitHub `bog5d/bog-vocab-tracker` | 直接对话 | 游戏化伴学 |
| **Engcjd_bot 引擎** (旧) | SQLite `vocab.db` | @Engcjd_bot | Telegram bot 快速录入 |

## Hermes 对话引擎架构

```
波总 ↔ Hermes (直接对话)
         ↓
  GitHub: bog5d/bog-vocab-tracker
  ├── data/words.json      (词库主表)
  ├── data/progress.json   (进度/段位/估分)
  ├── data/sessions.json   (学习记录)
  └── data/config.json     (游戏规则)
```

## 词库预设流程（从零搭建 1500 核心词）

1. **建立 GitHub 仓库**：`gh repo create bog-vocab-tracker --private`
2. **初始化数据文件**：`words.json`(空词库) + `progress.json`(快照) + `sessions.json`(记录) + `config.json`(规则引擎)
3. **批量生成核心词表**：分成 A-C / D-H / I-M / N-P / Q-S / T-Z 六大块，每块用 `execute_code` 内联生成
4. **合并与去重**：读取已有 `words.json`，用 `lower()` 统一 key 去重，新增词追加
5. **分类分级**：Lv.1 超高频(>50 次) ~400 词，Lv.2 高频(20-50) ~500 词，Lv.3+ 中低频 ~600 词
6. **Git push**：合并后立即推送，覆盖 ~1300+ 词后继续补充到 1500

批量生成技巧：`execute_code` 沙箱中若代码超长，分段写入临时 JSON 文件 `_part_*.json`，最后读入合并。

## 核心能力

### 0. 段位系统（游戏化主驱动力）

| 段位 | 覆盖率门槛 | 掌握率门槛 |
|------|-----------|-----------|
| 青铜 | 0% | 0% |
| 白银 | 10% | 30% |
| 黄金 | 25% | 45% |
| 铂金 | 40% | 55% |
| 钻石 | 60% | 70% |
| 王者 | 80% | 85% |
| 考研战神 | 100% | 90%+ |

积分规则：
- 答对 +10 / 新词发现 +20
- 连击 3 次 ×1.5, 5 次 ×2, 10 次 ×3
- 估分公式：`25 + (核心词覆盖率 × 0.4 + 掌握率 × 0.6) × 75`

每 5 天或覆盖率每涨 10% 触发抽样测试（抽 30 词）重新估分。

### 0.5 Grillme 适配 (Telegram 无 clarify 工具时)

用 A/B/C/D/E 内联选项代替 clarify 工具：
```
A. xxx
B. xxx
C. xxx
D. xxx
E. 其他，你说
```
每波之间输出"中间总结"结构（已确认事实 + 假设 + 风险→下一波问题），最终输出"完整画像"。

### 1. 单词入库
用户发送单词 → 自动存入词库：
```bash
python3 ~/.hermes/scripts/english_tutor/engine.py add <word> <meaning>
```
支持批量：多行输入，每行一个单词

### 2. 词汇量统计
```bash
python3 ~/.hermes/scripts/english_tutor/engine.py stats
```
返回：总词数、已掌握、学习中、待复习、今日复习数、考研覆盖率、预估分数区间

### 3. 闪卡测试
```bash
python3 ~/.hermes/scripts/english_tutor/engine.py quiz
```
返回 5 个待复习单词。用户回答后调用：
```bash
python3 ~/.hermes/scripts/english_tutor/engine.py review <word_id> <quality>
```
quality: 0=全忘 1=看答案才想起 2=犹豫后对 3=难但对 4=犹豫后对 5=秒答

### 4. SM-2 遗忘曲线
- quality≥3 → 间隔增长（1→6→15→38→...）
- quality<3 → 重置间隔为 1 天
- 5 次连续正确 → 标记 mastered

## 交互协议

当用户在 @Engcjd_bot 发送以下内容时：

| 用户输入 | AI 动作 |
|---------|--------|
| 单个英文单词 | 添加到词库，回复确认 + 当前统计 |
| "测试" / "quiz" / "闪卡" | 出 5 个待复习单词 |
| "A" / "B" / "C" / "D" / "F" | 提交评分（A=5,B=4,C=3,D=2,F=1） |
| "进度" / "stats" / "统计" | 返回完整词汇量报告 |
| "预估" / "估分" | 返回考研分数估算 |

## 评分标准

- A (5): 秒答，完美
- B (4): 犹豫后答对
- C (3): 答对但有困难
- D (2): 答错，但看到答案觉得简单
- F (1): 答错，看到答案都没印象

## 数据文件

- 词库: `~/.hermes/scripts/english_tutor/vocab.db`
- 引擎: `~/.hermes/scripts/english_tutor/engine.py`
- 已预置 20 个考研高频词作为种子

## Anki txt 导入流水线

当用户发送 Anki 导出的 `.txt` 文件时：

1. **解析**：手动 tab-split（不用 csv.reader，引号会炸），跳过 `#` 开头行
2. **分类**：跳过中文开头卡片（`（真题原句` / `骨架解析`）和语法卡片（含 `Kaoyan Syntax`/`同位语`/`公式`）
3. **提取单词**：regex `^([a-zA-Z][a-zA-Z\s\-/()]+?)(?:\s*(?:/\S+?/)?\s*(?:Kaoyan|考研|<br>|$))`
4. **去重小写**：统一 lower
5. **核心词匹配**：内置 1500 考研高频词表做命中判定，分 Lv.1(>50次)/2(20-50)/3(<20)
6. **写入** words.json + progress.json → git push

## 铁律

- 单词统一小写存储
- 重复单词不报错，merge 历史数据
- GitHub 是单一事实源，每次数据变更后立即 git push
- 统计包含考研 1500 核心词覆盖率估算
- 游戏化元素：段位(A.青铜→B.白银→C.黄金→D.铂金→E.钻石→F.王者→G.考研战神)、积分、连击翻倍
