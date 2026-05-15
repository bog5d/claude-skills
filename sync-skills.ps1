# sync-skills.ps1 v2
# Skills (public: bog5d/claude-skills) + Memory (private: bog5d/wangbo-brain)
#
# Usage:
#   .\sync-skills.ps1              # auto (full sync)
#   .\sync-skills.ps1 push         # push skills only
#   .\sync-skills.ps1 pull         # pull skills + sync to Cursor
#   .\sync-skills.ps1 memory       # sync memory only
#   .\sync-skills.ps1 status       # show status dashboard
#   .\sync-skills.ps1 auto         # full sync (skills + memory)

param([string]$Mode = "auto")

# ── Paths ────────────────────────────────────────────────────────────────────
$CLAUDE_SKILLS  = "$env:USERPROFILE\.claude\skills"
$CURSOR_SKILLS  = "$env:USERPROFILE\.cursor\skills"
$BRAIN_PATH     = "$env:USERPROFILE\.wangbo-brain"
$MEMORY_SRC     = "$env:USERPROFILE\.claude\projects\D--AI-Workspaces\memory"
$MEMORY_DST     = "$BRAIN_PATH\memory\claude-code"
$LOG_FILE       = "$env:USERPROFILE\.claude\skills-sync.log"

# ── Fix encoding (prevent garbled log) ───────────────────────────────────────
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding           = [System.Text.Encoding]::UTF8

function Log {
    param([string]$msg)
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
    Write-Host $line
    $line | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
}

function Run-Git {
    # Suppresses red stderr (git progress), only fails on actual errors
    param([string[]]$GitArgs)
    $result = & git @GitArgs 2>&1
    return ($result -join "`n")
}

# ── 1. PUSH Skills: ~/.claude/skills -> GitHub (master) ──────────────────────
function Push-Skills {
    Log "=== PUSH: Skills -> GitHub (bog5d/claude-skills) ==="
    Set-Location $CLAUDE_SKILLS
    Run-Git "add", "-A" | Out-Null
    $changed = (Run-Git "diff", "--cached", "--name-only").Trim()
    if ($changed) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        Run-Git "commit", "-m", "auto-sync: $stamp" | Out-Null
        Run-Git "push", "origin", "master" | Out-Null
        $count = ($changed -split "`n" | Where-Object { $_ }).Count
        Log "Skills pushed: $count files changed"
    } else {
        Log "Skills: no changes, skip push"
    }
}

# ── 2. PULL Skills: GitHub -> ~/.claude/skills ───────────────────────────────
function Pull-Skills {
    Log "=== PULL: GitHub -> Skills ==="
    Set-Location $CLAUDE_SKILLS
    $result = Run-Git "pull", "origin", "master"
    if ($result -match "Already up to date") {
        Log "Skills: already up to date"
    } else {
        Log "Skills updated"
    }
}

# ── 3. SYNC Skills: ~/.claude/skills -> ~/.cursor/skills ─────────────────────
function Sync-ToCursor {
    Log "=== SYNC: Skills -> Cursor ==="
    if (-not (Test-Path $CURSOR_SKILLS)) {
        New-Item -ItemType Directory -Path $CURSOR_SKILLS -Force | Out-Null
    }
    Get-ChildItem $CLAUDE_SKILLS -Directory | Where-Object { $_.Name -notmatch "^\." } | ForEach-Object {
        $skillMd = Join-Path $_.FullName "SKILL.md"
        if (-not (Test-Path $skillMd)) { return }
        $dst = Join-Path $CURSOR_SKILLS $_.Name
        if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst -Force | Out-Null }
        Get-ChildItem $_.FullName -File | Where-Object {
            $_.Length -lt 512000 -and
            $_.Extension -notin @(".png",".jpg",".jpeg",".gif",".webp",".mp4",".zip",".exe")
        } | ForEach-Object {
            Copy-Item $_.FullName (Join-Path $dst $_.Name) -Force
        }
        Log "  -> Cursor: $($_.Name)"
    }
}

# ── 4. MEMORY: claude/memory -> wangbo-brain -> GitHub (main) ────────────────
function Sync-Memory {
    Log "=== MEMORY: Claude -> Brain -> GitHub (bog5d/wangbo-brain) ==="

    if (-not (Test-Path "$BRAIN_PATH\.git")) {
        Log "Brain repo not found, cloning..."
        Run-Git "clone", "https://github.com/bog5d/wangbo-brain.git", $BRAIN_PATH | Out-Null
    }

    Set-Location $BRAIN_PATH
    $pullResult = Run-Git "pull", "origin", "main"
    if ($pullResult -notmatch "Already up to date") {
        Log "Brain: pulled updates from GitHub"
    }

    if (Test-Path $MEMORY_SRC) {
        if (-not (Test-Path $MEMORY_DST)) {
            New-Item -ItemType Directory -Path $MEMORY_DST -Force | Out-Null
        }
        Copy-Item "$MEMORY_SRC\*" $MEMORY_DST -Force -Recurse
        Log "Memory files copied to Brain"
    } else {
        Log "WARNING: memory source not found: $MEMORY_SRC"
    }

    Set-Location $BRAIN_PATH
    Run-Git "add", "-A" | Out-Null
    $changed = (Run-Git "diff", "--cached", "--name-only").Trim()
    if ($changed) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        Run-Git "commit", "-m", "memory-sync: $stamp" | Out-Null
        Run-Git "push", "origin", "main" | Out-Null
        $count = ($changed -split "`n" | Where-Object { $_ }).Count
        Log "Memory pushed: $count files"
    } else {
        Log "Memory: no changes, skip push"
    }
}

# ── 5. STATUS dashboard ───────────────────────────────────────────────────────
function Show-Status {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Set-Location $CLAUDE_SKILLS

    $skillCount = (Get-ChildItem $CLAUDE_SKILLS -Recurse -Filter "SKILL.md" | Measure-Object).Count
    $topSkills  = Get-ChildItem $CLAUDE_SKILLS -Directory | Where-Object { $_.Name -notmatch "^\." }
    $lastCommit = Run-Git "log", "--oneline", "-1"
    $lastTime   = Run-Git "log", "-1", "--format=%ci"

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "   wangbo AI Brain - Sync Status" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [Skills] bog5d/claude-skills (public)" -ForegroundColor Yellow
    Write-Host "  Count       : $skillCount SKILL.md files" -ForegroundColor Green
    Write-Host "  Last sync   : $lastTime" -ForegroundColor Green
    Write-Host "  Last commit : $lastCommit" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Skills list:" -ForegroundColor White
    $topSkills | ForEach-Object {
        $sub = (Get-ChildItem $_.FullName -Recurse -Filter "SKILL.md" | Measure-Object).Count
        $label = if ($sub -gt 1) { "    + $($_.Name)  ($sub sub-skills)" } else { "    + $($_.Name)" }
        Write-Host $label -ForegroundColor Gray
    }

    Write-Host ""
    Write-Host "  [Memory] bog5d/wangbo-brain (PRIVATE)" -ForegroundColor Yellow
    if (Test-Path $BRAIN_PATH) {
        Set-Location $BRAIN_PATH
        $memFiles    = (Get-ChildItem "$BRAIN_PATH\memory\claude-code" -File -ErrorAction SilentlyContinue | Measure-Object).Count
        $brainCommit = Run-Git "log", "--oneline", "-1"
        Write-Host "  Memory files: $memFiles" -ForegroundColor Green
        Write-Host "  Last commit : $brainCommit" -ForegroundColor DarkGray
    } else {
        Write-Host "  Brain repo not cloned (run auto mode to initialize)" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "  [Cursor sync]" -ForegroundColor Yellow
    if (Test-Path $CURSOR_SKILLS) {
        $cursorCount = (Get-ChildItem $CURSOR_SKILLS -Directory | Measure-Object).Count
        Write-Host "  ~/.cursor/skills/ ($cursorCount packages)" -ForegroundColor Green
    } else {
        Write-Host "  Not synced yet" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "  [Recent sync events]" -ForegroundColor Yellow
    if (Test-Path $LOG_FILE) {
        Get-Content $LOG_FILE -Encoding UTF8 | Where-Object { $_ -match "===" } | Select-Object -Last 6 |
            ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
    }
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
}

# ── Main ──────────────────────────────────────────────────────────────────────
switch ($Mode.ToLower()) {
    "push"   { Push-Skills }
    "pull"   { Pull-Skills; Sync-ToCursor }
    "sync"   { Sync-ToCursor }
    "memory" { Sync-Memory }
    "status" { Show-Status }
    "auto"   {
        Push-Skills
        Pull-Skills
        Sync-ToCursor
        Sync-Memory
        Log "=== All done (Skills + Memory) ==="
    }
    default  { Write-Host "Usage: .\sync-skills.ps1 [auto|push|pull|sync|memory|status]" }
}
