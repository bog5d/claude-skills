---
name: skillopt-integration
description: Optimize Hermes skills with the SkillOpt methodology — test cases, ReflACT pipeline, validation gates, and weekly cron-based improvement loop.
---

# SkillOpt Integration

## Overview

SkillOpt is Microsoft's open-source framework that applies neural-network training discipline to optimizing agent skill documents. Instead of hand-tuning prompts by feel, it uses epochs, learning rates, validation gates, and held-out evaluation sets.

We've integrated the methodology into Hermes — not calling the full SkillOpt training loop on every edit, but embedding the key disciplines:
- **Test cases per skill** (`references/test-cases.md`) — the validation set
- **Bounded edits** — max 2-3 changes per optimization round (text learning rate)
- **Validation gate** — edits accepted only if they strictly improve the held-out score
- **Weekly cron** — automated reflection → analysis → suggestion cycle

## When to Use

- You just modified a skill and want to verify it's actually better, not just different
- The weekly `skill-optimizer-weekly` cron flagged improvement suggestions
- You're adding a new skill and want to bootstrap it with the SkillOpt methodology

## Test Case Discipline

Every skill under active optimization should have a `references/test-cases.md` with:
- 3-5 scenarios covering high, medium, and edge cases
- Each scenario: trigger input → expected behavior → anti-pattern
- Scoring rubric (0/1/2 scale per case, ≥70% to pass)

### Test Case Template

```
# Test Cases — <skill-name>

## TC-XX-01: <scenario name>

**触发输入：** <what the user says>

**期望行为：** <what the agent MUST do>

**反模式（不合格）：** <what the agent MUST NOT do>
```

## ReflACT Pipeline (Six Stages)

Adapted from SkillOpt's paper. Each optimization round:

1. **Rollout** — Run the skill against test cases, collect scores
2. **Reflect** — Analyze which test cases scored < 2, identify root causes
3. **Analyze** — Generate targeted patches (add/delete/replace specific sections)
4. **Merge** — Combine patches into a candidate skill document
5. **Rank** — If edits exceed text learning rate budget, keep only top-N
6. **Gate** — Validate candidate against test cases. Accept ONLY if score strictly improves. Otherwise discard.

This is implemented in `/Users/mac/.hermes/scripts/skillopt_demo.py`.

## Weekly Optimizer Cron

Job ID: `34cce28829e8`  
Schedule: Sundays at 10:00 CST  
Script: `/Users/mac/.hermes/scripts/skill_optimizer_weekly.py`

The cron:
1. Finds skills modified in the past week
2. Checks test case coverage
3. Generates improvement suggestions (max 2 per week — text LR)
4. Only suggests changes with concrete evidence from session trajectories

Suggestions that don't pass the validation gate go into a rejected-edit buffer. After 3 consecutive rejections, the suggestion is permanently removed.

## Skills Under Active Optimization

| Skill | Test Cases | Last Score | Cron Coverage |
|-------|-----------|------------|---------------|
| `three-layer-execution-wall` | 5 (TC-3L-01~05) | 10/10 | ✅ |
| `github-pr-workflow` | 5 (TC-PR-01~05) | — | ✅ |
| `systematic-debugging` | 5 (TC-DBG-01~05) | 10/10 | ✅ |

## Adding a New Skill to the Pipeline

```bash
# 1. Create test cases
cp /Users/mac/.hermes/profiles/her-m2/skills/three-layer-execution-wall/references/test-cases.md \
   /path/to/new-skill/references/test-cases.md
# Edit the test cases for the new skill

# 2. Register in the weekly optimizer
# Edit /Users/mac/.hermes/scripts/skill_optimizer_weekly.py
# Add to SKILLS_WITH_TESTS dict

# 3. Run a baseline evaluation
/Users/mac/.hermes/hermes-agent/venv/bin/python3 \
  /Users/mac/.hermes/scripts/skillopt_demo.py
```

## Pitfalls

- **Heuristic scoring is cheap but imprecise.** The demo script uses keyword matching — good for catching structural gaps, not semantic correctness. For critical skills, consider calling the actual agent against real scenarios.
- **Text learning rate must be enforced.** Don't make 5+ edits to a skill in one pass — that's the equivalent of setting LR too high. Max 3 per round.
- **Gate must be strict.** If the candidate skill doesn't strictly improve the score, discard it. "It feels better" is not a valid criterion.
- **SkillOpt pip install requires Python ≥ 3.10.** Use the Hermes venv: `/Users/mac/.hermes/hermes-agent/venv/bin/pip3`.
