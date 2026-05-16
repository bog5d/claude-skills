#!/bin/bash
# Cross-profile skills synchronizer
# Bidirectional merge: newer wins, nothing deleted, new skills copied both ways.
# Usage: bash sync_skills_cross_profile.sh [SRC1] [SRC2]
# Default: ~/.hermes/skills ↔ ~/.hermes/profiles/her-m2/skills

set -euo pipefail

SRC1="${1:-$HOME/.hermes/skills}"
SRC2="${2:-$HOME/.hermes/profiles/her-m2/skills}"
LOG="$HOME/.hermes/logs/sync_skills.log"

mkdir -p "$(dirname "$LOG")"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

log "=== Sync started ==="

# Find all skill directories (those containing SKILL.md)
find_skills() {
    find "$1" -name "SKILL.md" -not -path "*/.git/*" -not -path "*/.hub/*" 2>/dev/null \
        | sed "s|/SKILL.md$||" | sed "s|^$1/||" | sort -u
}

updated=0
copied=0

while IFS= read -r skill; do
    d1="$SRC1/$skill"
    d2="$SRC2/$skill"

    if [ -d "$d1" ] && [ -d "$d2" ]; then
        # Both exist — compare SKILL.md mtime, newer wins
        t1=$(stat -f %m "$d1/SKILL.md" 2>/dev/null || stat -c %Y "$d1/SKILL.md" 2>/dev/null || echo 0)
        t2=$(stat -f %m "$d2/SKILL.md" 2>/dev/null || stat -c %Y "$d2/SKILL.md" 2>/dev/null || echo 0)

        if [ "$t1" -gt "$t2" ]; then
            rsync -a --delete "$d1/" "$d2/"
            log "  ← SRC1 → SRC2: $skill"
            updated=$((updated + 1))
        elif [ "$t2" -gt "$t1" ]; then
            rsync -a --delete "$d2/" "$d1/"
            log "  ← SRC2 → SRC1: $skill"
            updated=$((updated + 1))
        fi
    elif [ -d "$d1" ]; then
        # Only in SRC1 — copy to SRC2
        rsync -a "$d1/" "$d2/"
        log "  + SRC1 → SRC2: $skill"
        copied=$((copied + 1))
    elif [ -d "$d2" ]; then
        # Only in SRC2 — copy to SRC1
        rsync -a "$d2/" "$d1/"
        log "  + SRC2 → SRC1: $skill"
        copied=$((copied + 1))
    fi
done < <( { find_skills "$SRC1"; find_skills "$SRC2"; } | sort -u )

log "Done — updated: $updated, copied: $copied"
log "=== Sync complete ==="
