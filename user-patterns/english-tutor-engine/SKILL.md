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

## 系统架构

```
Telegram @Engcjd_bot
        ↓
  接收单词/指令
        ↓
  ~/.hermes/scripts/english_tutor/engine.py
        ↓
  SQLite 词库 (vocab.db) + SM-2 遗忘曲线
        ↓
  反馈 ← 词汇量/进度/测试
```

## 核心能力

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

## 铁律

- 单词统一小写存储
- 重复单词不报错，提示"已在词库"
- 每次测试后自动更新间隔和熟练度
- 统计包含考研 5500 词覆盖率估算
