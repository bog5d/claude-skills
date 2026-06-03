---
name: vocab-batch-challenge
description: Generate 6-word vocabulary challenges for kaoyan English with Progressive or Straight Batch modes. Anki-first selection, SM-2 scheduling, 5-layer explanations. Full spec in references-progressive-mode-spec.
category: english-tutor
---

# Vocab Batch Challenge Generator

**CRITICAL RULE**: Challenge words MUST be presented WITHOUT Chinese meanings. The whole point is to TEST recall. Chinese meanings only appear in the post-answer explanation phase.

## Workflow

### Phase 1: Generate Challenge (no meanings shown) — FAST PATH FIRST

**Default (10–30s):** one terminal only, no Agent tool loop:

```bash
/Users/mac/.hermes/hermes-agent/venv/bin/python3 /Users/mac/.hermes/profiles/english-tutor/bin/fast_vocab_round.py
```

Paste stdout to Telegram. Script sets `vocab_batch.json` + `coordinator` english lock.

**Fallback** (only if script exits non-zero): pull `words.json` via curl + manual SM-2 select (legacy steps below).

1. Pull latest `words.json`, `progress.json` from GitHub `bog5d/bog-vocab-tracker` (repo is PRIVATE, use PAT) — files live under `data/` directory
2. Apply SM-2 priority scheduling to select 6 words
3. Present ONLY: `{index}. {word}  {phonetic}` — NO meanings, NO hints
4. Wait for user to reply with 6 Chinese meanings

### Phase 2: Score + Explain (single execute_code call)
After user replies with 6 answers, process everything in ONE execute_code call:
- Score each answer (correct/incorrect, record exact user response)
- Update SM-2 model (interval, EF, mastery)
- Push updated data back to GitHub
- Generate ALL 5-layer explanations for EVERY word (correct or incorrect):
  1. 词根拆解 + 同源词族
  2. 演化链
  3. 视觉锚点
  4. 原卡时空背景 (if available from Anki)
  5. 考研语境锚

### Phase 3: Present Results
- First: clear score summary (correct/total) — welded with dividers, never buried
- Then: full 5-layer explanations for ALL 6 words
- Then: gamification panel using `gamification_v2.py`:
  ```python
  g, ranked_up, chronicle_path, challenge_info = update_after_session(g, session_stats, session_words)
  # NOTE: 4-value return! challenge_info may be None if no rank-up
  save_gam(g)
  print(gen_panel(g))
  if ranked_up and chronicle_path:
      # Deliver chronicle HTML + timeline HTML
      print(f"__CHRONICLE__:{chronicle_path}")
  if challenge_info:
      # Offer a sub-tier challenge
      print(f"🎯 晋升挑战: {challenge_info['icon']} {challenge_info['name']}")
      print(f"   {challenge_info['desc']}")
      print(f"   题目: {challenge_info['clue']}")
      # Wait for user to attempt the challenge
  ```

## Pitfalls
- **NEVER show Chinese meanings in Phase 1** — this is the #1 recurring error
- After each session, update `gamification.json` streak/last_session_date and re-check badges
- The repo path is `data/words.json` not root-level; use GitHub Contents API path `bog5d/bog-vocab-tracker/contents/data/words.json`
- progress.json may have few entries; default new words to SM-2 initial state
- Use `Accept: application/vnd.github.v3.raw` header for GitHub API — or download with `curl -o /tmp/file.json` for speed (git clone often times out on this environment)
- All scoring + explanations + GitHub push must fit in ONE execute_code call for latency
- **Batch word recovery**: when user replies with answers, the current batch words are NOT stored in sessions.json (sessions array is often empty). Use `session_search(query="挑战包")` to find the most recent challenge presentation and extract the 6 words from the assistant's message. This session proved: session_search is the reliable fallback for batch word recovery.
- **Phonetic fallback**: `words.json` entries may have empty `phonetic` fields. If phonetic is missing from the data, extract it from the original challenge presentation in session history, or use the built-in phonetics reference in `references/phonetics.md`.
- Do NOT try `git clone` of the entire repo — it frequently times out (>60s). Always use individual file downloads via `curl` with the GitHub API raw endpoint.
- **MEDIA file delivery (CRITICAL)**: When sending chronicle HTML or screenshots via MEDIA tag, `/tmp/` is NOT in the whitelist — files sent from `/tmp/` are silently dropped. Always `cp` to `~/.hermes/cache/screenshots/` (images) or `~/.hermes/cache/documents/` (HTML/docs) first. Use ASCII filenames. Load `media-file-delivery` skill for full rules.
- Do NOT try `git clone` of the entire repo — it frequently times out (>60s). Always use individual file downloads via `curl` with the GitHub API raw endpoint.

## Progressive Challenge Mode (NEW)

A multi-turn warmup-to-burst format for session 1 of the day. Designed to eliminate the psychological pressure of 6 words at once.

**Structure per session (3 rounds = 6 words):**
- Round 1: 1 word → score + explain → present Round 2
- Round 2: 2 words → score + explain → present Round 3
- Round 3: 3 words → score + explain → FULL SESSION SUMMARY + gamification blast

**State tracking** uses `~/.hermes/profiles/english-tutor/state/vocab_progressive.json`:
```json
{
  "session_id": "prog-20260528-HHMMSS",
  "round": 1,           // current round (1-3)
  "total_rounds": 3,
  "all_words": [...],   // all 6 words in order
  "all_words_data": {}, // SM-2 metadata per word
  "round_words": {      // word assignments per round
    "1": [{"word": "...", "phonetic": "..."}],
    "2": [...],
    "3": [...]
  },
  "scores": {},         // accumulates across rounds
  "started_at": "...",
  "mode": "progressive"
}
```

**Per-turn workflow:**
1. If no state file → init new session (pull words, select 6, assign rounds, save state, present Round 1)
2. If state.round < 3 → score current round, update SM-2, push GitHub, increment round, present next batch
3. If state.round == 3 → score final round, update SM-2, push GitHub, present FULL summary + delete state file

**Progressive difficulty**: within the 6-word batch, sort by core_level ascending so easier words come first.

## Straight Batch Mode

Session 2 of the day (or standalone). Present all 6 words at once, user answers all 6, single scoring pass. State file: `state/vocab_batch.json`. Simpler — no multi-turn tracking needed.

## BOSS Mode — Nightmare Word Round 👾

When active nightmare words ≥ 3, offer BOSS mode before starting any session.

**Eligibility check (before Phase 1):**
```python
import sys; sys.path.insert(0, "/Users/mac/.hermes/profiles/english-tutor/state")
from nightmare_boss import is_boss_eligible, get_active_nightmares, generate_boss_round

if is_boss_eligible():
    nightmares = get_active_nightmares()
    # Ask user: "👾 {N}个噩梦词集结！要开BOSS局围剿吗？"
    # If yes → generate BOSS round → present 6 nightmare words
    # If no → proceed with regular session
```

**BOSS round flow:**
1. Generate BOSS state via `generate_boss_round()` → `state/vocab_boss.json`
2. Present all nightmare words (3-6, depends on active count) WITHOUT Chinese meanings
3. User answers → score via `nightmare_boss.process_boss_results()`
4. Apply clears via `nightmare_boss.apply_boss_clears()` → +3% progress per clear
5. Show BOSS panel via `nightmare_boss.gen_boss_panel()`
6. Full 5-layer explanations for ALL BOSS words
7. Then gamification panel as usual

**BOSS scoring differences from regular:**
- Correct on a nightmare word → word is CLEARED (no longer active) + **+3% rank progress**
- Wrong → nightmare stays active, no penalty beyond regular SM-2
- BOSS mode does NOT count toward daily session total (it's bonus content)

**Pitfalls:**
- BOSS state file at `state/vocab_boss.json` — clean up after scoring
- BOSS words also need SM-2 update + push to GitHub
- The gamification panel after BOSS round should reflect any new progress from clears
- If user declines BOSS, proceed with normal session — don't force it

## Daily Session Structure

```
Session 1: Progressive (1→2→3 = 6 words) — warmup
Session 2: Straight Batch (6 words) — burst
BOSS Mode: 3-6 nightmare words (when eligible) — bonus round
Daily minimum: 12 words (BOSS is extra)
```

## Sub-Rank System (青铜I→IV→白银)

Each session end calls `gamification_v2.gen_panel()` to display a sub-rank ladder:

```
🥉 青铜I · 入门者 → 青铜II · 积累者 → 青铜III · 突破者 → 青铜IV · 冲刺者 → 🥈 白银
```

Each sub-rank has unlock requirements checked automatically:
- 青铜II: 3 sessions, 2-day streak, 50% accuracy
- 青铜III: 5 sessions, 3-day streak, 50% accuracy, 3 nightmare words cleared
- 青铜IV: 8 sessions, 30 mastery50 words, 60% Anki coverage, boss fight
- 白银: 100% progress + all sub-rank conditions

Nightmare words: words missed 2+ times get marked "active". Clearing them gives +3% progress bonus.

## Anki-First Word Selection (MANDATORY)

User's Anki-imported words (source="anki_import", ~107 words) get TOP priority in selection:
1. Score all words with SM-2 priority function
2. Separate into `anki_words` and `preset_words` pools
3. Pick from anki pool first (top-N candidates, shuffled for variety)
4. Only fill remaining slots from preset pool
5. Exclude words just studied in the current day's other session

Selection output must report the Anki ratio (e.g. "6/6 from Anki").

## Network: Use terminal+curl, NOT execute_code urllib

`execute_code` sandbox on macOS hits SSL certificate verification errors (`CERTIFICATE_VERIFY_FAILED`). Use `terminal()` with `curl` + PAT header + `Accept: application/vnd.github.v3.raw` instead. Download to `/tmp/vocab/` for processing in a follow-up `execute_code` call.

Pattern:
```bash
curl -s -o /tmp/vocab/words.json \
  -H "Authorization: token $PAT" \
  -H "Accept: application/vnd.github.v3.raw" \
  "https://api.github.com/repos/bog5d/bog-vocab-tracker/contents/data/words.json"
```

## Key User Preferences
- User is 波总 (Bog), hates latency — target <30s end-to-end
- All 6 words get full 5-layer explanations, regardless of correct/incorrect
- Score verdict must appear FIRST before explanations (用分隔线焊死)
- User explicitly wants Duolingo-style gamification: progress bars, badges, streak pressure, session summaries with achievement feel
- When user answers "不认识" for multiple words, score all as wrong (q=0) but still provide full 5-layer explanations — honesty is rewarded with learning
