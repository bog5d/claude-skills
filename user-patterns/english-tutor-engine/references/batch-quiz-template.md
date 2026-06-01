# Batch Quiz Mode — 6词冲刺包模板

Use this template structure for every batch quiz session (6 words, one-shot).

## Interaction Flow

```
Agent: 发 6 词（纯单词+音标，无提示含义）
User:  回复 6 答案（"1:xxx 2:yyy ... 6:zzz"）
Agent: execute_code(1次) → 完整判分+5层讲解+进度报告
```

## Execute Code Template (Pseudo)

```python
# === STEP 1: FETCH ===
import urllib.request, json, base64, ssl
from datetime import date
token = "ghp_YOUR_TOKEN_HERE"
# fetch: words.json, progress.json, config.json, sessions.json
# get SHA for push

# === STEP 2: PARSE ANSWERS ===
# Accept: "1: 纪律 2: 缓解 ..." or "1. 纪律 2. 缓解 ..."
# Use classify() with keyword matching, not exact string comparison
def classify(word, resp):
    keys = {"discipline": ["纪律","学科","训练"], ...}
    return any(k in resp for k in keys.get(word, []))

# === STEP 3: SM-2 UPDATE (6x) ===
# Each word: update ef/interval/mastery, append to history

# === STEP 4: STATS ===
# Reconstruct total_correct/mistakes from words[*].history
# NOT from snapshot! snapshot may be stale.

# avg_mastery = sum(mastery for w in reviewed) / len(reviewed)  # PRACTICED ONLY

# score = 25 + (coverage * 0.4 + practiced_avg_mastery * 0.6) * 75

# === STEP 5: EVENTS ===
# sub-milestones (every 3 words met)
# main milestones (5/10/20/50/100/200/500/1000)
# boss check (every 10 correct)
# streak chest

# === STEP 6: PUSH ===
# words.json + progress.json + sessions.json

# === STEP 7: PRECEN NEXT BATCH ===
# Pre-select 6 words for next round (weakest due first)
```

## Key Constants

- Batch size: 6 words
- Token: ghp_YOUR_TOKEN_HERE
- GitHub repo: bog5d/bog-vocab-tracker
- Data path: data/words.json, data/progress.json, data/sessions.json, data/config.json
- SSL: check_hostname=False, verify_mode=CERT_NONE (sandbox compat)

## Classification Keywords (per word)

Discovered through testing: use broad keyword matching.

```python
# If the user says "规则纪律" and the answer key says "纪律", that's a match.
# Don't require exact match — they may write multiple keywords.

classify_map = {
    "discipline": ["纪律", "学科", "训练", "约束"],
    "alleviate": ["减轻", "缓解", "减缓"],
    "atmosphere": ["气氛", "氛围", "大气", "大气层"],
    "audit": ["审计", "查账", "旁听"],
    "authentic": ["真实", "原本", "真正", "原汁原味"],
    "barrier": ["障碍", "壁垒", "栏杆", "屏障"],
    "bottleneck": ["瓶颈", "颈部", "瓶颈口"],
    "cognitive": ["认知", "认识", "感知"],
    "companion": ["同伴", "伙伴", "伴侣"],
    "compliance": ["合规", "遵从", "顺从"],
    "component": ["零件", "部件", "成分", "组件"],
    "congestion": ["堵塞", "拥挤", "拥堵"],
    "conventional": ["传统", "惯例", "常规"],
    "dilemma": ["进退两难", "窘境", "两难"],
}
```

## Response Format

After execute_code, render as:

```
---
## ⚔️ 判分总表

| # | 词 | 结果 | ... (Telegram-friendly table)

---

## 🔬 5层讲解 (6 words)
[1. 词根拆解 2. 演化链 3. 视觉锚点 4. 原卡时空背景 5. 考研锚]

---

## 📊 进度环
```

Do NOT include the answer key in the question message. The user MUST recall from memory.
