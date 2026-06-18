# Progressive Challenge Mode — Full Spec

## State File Schema

### Progressive mode: `state/vocab_progressive.json`
```json
{
  "session_id": "prog-20260528-143022",
  "round": 1,
  "total_rounds": 3,
  "all_words": ["facility", "equilibrium", "distort", "seamless", "memorable", "electric razor"],
  "all_words_data": {
    "facility": {"core_level": 2, "review_count": 0, "mastery": 0.0, "source": "anki_import", "ef": 2.5, "interval": 0, "phonetic": "/fəˈsɪləti/"}
  },
  "round_words": {
    "1": [{"word": "facility", "phonetic": "/fəˈsɪləti/"}],
    "2": [{"word": "equilibrium", "phonetic": "/ˌiːkwɪˈlɪbriəm/"}, {"word": "distort", "phonetic": "/dɪˈstɔːt/"}],
    "3": [{"word": "seamless", "phonetic": "/ˈsiːmləs/"}, {"word": "memorable", "phonetic": "/ˈmemərəbəl/"}, {"word": "electric razor", "phonetic": ""}]
  },
  "scores": {
    "facility": {"word": "facility", "user_answer": "事实真相", "correct": false, "quality": 1, "error_type": "词形混淆（与fact混淆）", "timestamp": "..."}
  },
  "started_at": "2026-05-28T14:30:22",
  "mode": "progressive",
  "selection_policy": "anki_first",
  "daily_session": 1
}
```

### Batch mode: `state/vocab_batch.json`
```json
{
  "session_id": "batch-20260528-144500",
  "mode": "batch",
  "round": 1,
  "total_rounds": 1,
  "all_words": ["mesh", "precise", "adjacent", "hybrid", "rhythmic", "weathered"],
  "all_words_data": {},
  "scores": {},
  "started_at": "...",
  "daily_session": 2
}
```

## Per-Turn Execution Flow

### Turn 1: Init Session + Present Round 1

```
1. curl download words.json + progress.json → /tmp/vocab/
2. execute_code:
   a. Load word data
   b. Anki-first SM-2 selection (6 words)
   c. Sort by core_level ascending
   d. Assign to rounds: [1], [2,3], [4,5,6]
   e. Save state to ~/.hermes/profiles/english-tutor/state/vocab_progressive.json
   f. Output: round 1 word + phonetic
3. Present: "ROUND 1/3 · {word} {phonetic} · 输入中文释义"
```

### Turn 2-N: Score + Advance

```
1. execute_code:
   a. Load state file
   b. Parse user's answers for current round
   c. Score each: quality (0=blackout, 1=confused, 5=correct)
   d. SM-2 update for each word in words.json
   e. Base64-encode + PUT to GitHub (words.json)
   f. Update state: state["round"] += 1, state["scores"][word] = {...}
   g. If round < 3: output next round words
   h. If round == 3: output session summary stats + delete state file
2. Present: score verdict → 5-layer explanations → next round words OR final summary
```

## SM-2 Quality Mapping

| User Response Pattern | Quality | Meaning |
|----------------------|---------|---------|
| Exact correct match | 5 | Perfect recall |
| Close but imprecise | 4 | Minor hesitation |
| Correct after struggle | 3 | Recalled with effort |
| Wrong but close (confused with similar word) | 1-2 | Partial trace |
| "不认识" / complete blackout | 0 | No memory trace |

## Scoring Edge Cases

- **"不认识" for multiple words**: score ALL as q=0, correct=false. Record exact string "不认识" as user_answer. Still provide full 5-layer explanations.
- **Confused with similar word** (e.g. precise→precious, facility→fact): score as q=1, record confusion in error_type. Include "you're thinking of X" diagnostic in explanation.
- **Partial correct** (e.g. "毗邻的挨着的" for adjacent): score as q=5 if meaning is essentially correct, even if multiple near-synonyms used.

## GitHub Push Pattern

```python
import base64
encoded = base64.b64encode(json.dumps(words_data, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8')
# GET current SHA
sha = json.loads(subprocess.run(["curl", "-s", "-H", f"Authorization: token {PAT}", url], capture_output=True, text=True).stdout)["sha"]
# PUT with SHA
body = json.dumps({"message": "progressive R2: word1 ✗ word2 ✓", "content": encoded, "sha": sha})
subprocess.run(["curl", "-s", "-X", "PUT", "-H", f"Authorization: token {PAT}", "-H", "Content-Type: application/json", "-d", body, url])
```

## Known Data Quirks

- **progress.json history**: `correct` field is sometimes a list of words (batch session recording) rather than a boolean. Do not rely on it for truth — use words.json's `review_count`/`correct_count` as the authoritative source.
- **progress.json history**: `word` field is "?" for batch-mode entries. Extract actual words from the `correct` array field, or from words.json `review_count > 0`.
- **sessions.json**: sessions array is often empty. Actual records live in words.json and progress.json.
