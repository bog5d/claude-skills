# Chronicle System Architecture

## File Map

```
state/
├── gamification.json          # Authoritative game state (v3 format)
│   ├── rank: "白银"           # Broad rank category
│   ├── sub_rank: "白银I"      # Specific tier (USE THIS for reports)
│   ├── rank_progress: 0.0     # Sub-rank progress [0-100], resets on rank-up
│   ├── stats: {...}            # Session counts, accuracy, anki coverage
│   ├── nightmare_words: {...}  # Per-word miss tracking
│   ├── streak / best_streak / total_xp / last_session_date
│   └── _version: 3            # Migrated from v2
│
├── rank_config.json           # Rank ladder definitions (READ-ONLY config)
│   ├── ranks[]: bronze→silver→gold→platinum→diamond→king→god
│   └── unlock_conditions per sub-tier
│
├── rank_timeline.json         # Immutable log of all rank-ups
│   └── rank_ups[]: {from, to, date, sessions, streak, xp}
│
├── gamification_v2.py         # Game engine (MUST call update_after_session)
│   ├── load() → _migrate() → returns dict
│   ├── update_after_session(g, stats, words) → (g, ranked_up, chronicle_path, challenge)
│   ├── gen_panel(g) → ASCII art gamification panel
│   └── save(g) → writes gamification.json
│
├── chronicle_generator.py     # v2: dual progress bars + territory + particles
│   ├── load_data() → gam, progress, words_data, achievements
│   ├── build_timeline_events() → session grouping from words.json history
│   └── generate_chronicle_html(from, to, from_name, to_name) → HTML string
│
├── chronicle_index_generator.py  # 勋章收藏室 master gallery
│   └── generate_index() → HTML with all milestone cards
│
├── chronicle_青铜II.html      # Generated on rank-up
├── chronicle_青铜III.html
├── chronicle_白银I.html
└── chronicle_index.html       # Updated on every rank-up
```

## Data Flow (Critical Path)

```
Session Complete
    │
    ├─► words.json (GitHub) ← updated with SM-2 + history
    │
    └─► update_after_session() ─ MUST RUN ─┐
         │                                  │
         ├─ streak += 1 (if consecutive)    │ SKIP = gamification freezes
         ├─ XP += session_gain              │ chronicles stop generating
         ├─ rank_progress += gain           │ reports show stale data
         ├─ nightmare tracking updated      │
         ├─ stats.* incremented             │
         │                                  │
         ├─ rank_progress ≥ 100?            │
         │   ├─ YES → rank up              │
         │   │   ├─ rank_timeline.json += 1 │
         │   │   ├─ chronicle_{rank}.html   │
         │   │   └─ chronicle_index.html    │
         │   └─ NO  → no rank change        │
         │                                  │
         └─ save gamification.json ◄────────┘
```

## Bug That Caused the 2026-06-06 Incident

**Root cause**: `update_after_session()` was never called after sessions.
- gamification.json frozen at May 31 data
- streak stuck at 1
- chronicles stopped generating
- Reports reading `rank` ("青铜") instead of `sub_rank` ("青铜III")

**Fix applied**:
1. Manually synced session data into gamification.json
2. Cleaned duplicate top-level fields (old v2 format leakage)
3. Updated skill to mandate `update_after_session()` call
4. Updated chronicle_generator to use `rank_config.json` not `sub_rank_system`
