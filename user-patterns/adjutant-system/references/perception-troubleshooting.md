# perception.py PATH RESOLUTION DEBUG

## Symptom
```
❌ git fetch 失败: [Errno 2] No such file or directory: '/Users/mac/.hermes/profiles/XXX/adjutant/repo/hermes-adjutant'
❌ advisor.py 不存在: /Users/mac/.hermes/profiles/XXX/adjutant/repo/hermes-adjutant/scripts/advisor.py
```

## Root Cause
`perception.py` resolves repo path as:
```python
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
ADJUTANT_HOME = HERMES_HOME / "adjutant"
REPO_DIR = ADJUTANT_HOME / "repo" / "hermes-adjutant"
```

When the cron job triggers from a different Hermes profile (e.g. `finance` profile with `HERMES_HOME=/Users/mac/.hermes/profiles/finance`), the resolved path points to a directory that doesn't have an adjutant setup.

## Quick Fix (cron command)
```cron
*/5 * * * * export HERMES_HOME=/Users/mac/.hermes && cd ~/.hermes/adjutant/repo/hermes-adjutant && python3 scripts/perception.py --once
```

## Robust Fix (perception.py patch)
Replace HERMES_HOME-based resolution with script-relative fallback:
```python
HERMES_HOME = Path(os.environ.get("HERMES_HOME", ""))
REPO_DIR = Path(__file__).resolve().parents[2]  # scripts/perception.py → repo root
if not (REPO_DIR / "status.json").exists():
    # Fallback to HERMES_HOME
    REPO_DIR = (HERMES_HOME or Path.home() / ".hermes") / "adjutant" / "repo" / "hermes-adjutant"
```

## Manual Fallback
When perception.py fails, manually execute:
```bash
cd /Users/mac/.hermes/profiles/her-m2/adjutant/repo/hermes-adjutant
git pull origin main
git status --porcelain   # check for uncommitted changes
# If changes exist:
git add -A && git commit -m "auto: perception sync $(date +%Y-%m-%dT%H:%M)" && git push origin main
```
