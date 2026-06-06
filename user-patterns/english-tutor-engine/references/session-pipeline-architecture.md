# 统一答题流水线架构

> 2026-06-06 建立。解决「LLM 手写 execute_code 导致游戏规则浮动」的核心问题。

## 问题

每次答题处理（判分→SM-2→五层讲解→gamification→GitHub push）完全靠 LLM 手写 execute_code。导致：
- 五层讲解有时候漏（Round 2 全对只给了 3 个重点词）
- Chronicle 投递有时候忘（晋升后没 cp 到 cache 发 MEDIA）
- 判分逻辑每次重写（可能不一致）
- 新 AI 接手无法立即工作

## 方案

**session_pipeline.py** — 单一 Python 脚本，吃进用户答案，吐出完整结果。

```
输入: python3 session_pipeline.py 2 '{"word1":"答案1",...}'

内部:
  1. PAT 从 git config 提取
  2. GitHub 拉取 words.json
  3. ANSWER_KEYWORDS 表判分（27 词内置）
  4. SM-2 更新每词
  5. FIVE_LAYER 表生成全部讲解（27 词内置，不论对错全出）
  6. gamification_v2.update_after_session()
  7. 段位晋升 → chronicle_generator → cp 至 cache → 索引更新
  8. GitHub push words.json
  9. Escalating 状态管理（轮次推进/结束清理）

输出: JSON {correct, total, explanations[], panel, chronicle_cache_path, _formatted, ...}
```

## LLM 角色最小化

LLM 只需：
1. `terminal()` 调用 session_pipeline.py
2. 解析 JSON，relay `_formatted` 字段
3. 如有 `tunnel_url` → 发 `{url}/chronicle_index.html`（单一网址，不是 MEDIA 碎片）
4. 如有 `next_round_words` → 展示下一轮题目

**不再手写 execute_code 做答题处理。**

## 新词维护

新增单词需同步：
1. `ANSWER_KEYWORDS["newword"] = ["关键词1","关键词2",...]`
2. `FIVE_LAYER["newword"] = {"root":"...","evolution":"...","anchor":"...","exam":"..."}`
