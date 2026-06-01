# Token Scrubbing Procedure

When GitHub push protection blocks pushes because skill files contain real
tokens (PATs, API keys, etc.), follow this procedure.

## Step 1: Diagnose

```bash
cd /Users/mac/.claude/skills
# Count unpushed commits
git log --oneline origin/master..HEAD | wc -l

# See the actual push error (remove 2>/dev/null from script first)
git push origin master 2>&1
```

GitHub will return exact file paths and line numbers for every secret.

## Step 2: Scrub tokens

For each location reported by GitHub, replace the real token with a placeholder:

```
Real token pattern:  ghp_YOUR_TOKEN_HERE
Replace with:        ghp_YOUR_TOKEN_HERE
```

Use `hermes_tools.patch` for targeted replacements per file — faster and
safer than sed/grep across the whole 195-skill tree.

## Step 3: Squash and push

The backlog of unpushed commits all carry tokens in their history.
Squash them into one clean commit:

```bash
cd /Users/mac/.claude/skills
git reset --soft origin/master
git commit -m "auto-sync: $(date '+%Y%m%d-%H%M%S') — Hermes skills → claude-skills (tokens scrubbed)"
git push origin master
```

## Step 4: Sync back to Hermes profiles

The claude-skills repo is downstream of Hermes profiles (Phase 3 rsyncs
Hermes → claude-skills). After scrubbing in claude-skills, propagate back
so the fix isn't overwritten next sync:

```bash
# Check all profile skill dirs for remaining tokens
rg 'ghp_[A-Za-z0-9]{36}' /Users/mac/.hermes/skills/ --include='*.md' -l
rg 'ghp_[A-Za-z0-9]{36}' /Users/mac/.hermes/profiles/her-m2/skills/ --include='*.md' -l
rg 'ghp_[A-Za-z0-9]{36}' /Users/mac/.hermes/hermes-agent/skills/ --include='*.md' -l
rg 'ghp_[A-Za-z0-9]{36}' /Users/mac/.hermes/profiles/english-tutor/skills/ --include='*.md' -l
```

If any found, scrub them the same way.

## Step 5: Verify

```bash
cd /Users/mac/.claude/skills
git log --oneline origin/master..HEAD | wc -l  # should be 0
```

## Known token locations (2026-06-02 incident)

These were the files that caused the 12-hour sync blackout:

| File | Line(s) | Token |
|------|---------|-------|
| `user-patterns/english-tutor-engine/SKILL.md` | 97, 436 | `ghp_YOUR_TOKEN_HERE` |
| `user-patterns/english-tutor-engine/references/batch-quiz-template.md` | 19, 57 | `ghp_YOUR_TOKEN_HERE` |
| `productivity/wordpress-management/references/relay-telegram-integration.md` | 111 | `ghp_YOUR_TOKEN_HERE` |

These tokens are now **revoked by GitHub** (push protection auto-revokes
detected tokens). They were embedded in code examples within skill docs —
never do this. Always use placeholders.
