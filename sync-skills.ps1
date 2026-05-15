# sync-skills.ps1 v2
# 统一同步脚本：Skills（公开）+ Memory（私有）→ GitHub + Cursor
#
# 用法:
#   .\sync-skills.ps1              # 默认 auto（全部同步）
#   .\sync-skills.ps1 push         # 只推送 skills
#   .\sync-skills.ps1 pull         # 只拉取 skills + 同步到 Cursor
#   .\sync-skills.ps1 memory       # 只同步 memory
#   .\sync-skills.ps1 status       # 查看状态
#   .\sync-skills.ps1 auto         # 完整同步（skills + memory）

param([string]$Mode = "auto")

# ── 路径配置 ─────────────────────────────────────────────────────────────────
$CLAUDE_SKILLS  = "$env:USERPROFILE\.claude\skills"
$CURSOR_SKILLS  = "$env:USERPROFILE\.cursor\skills"
$BRAIN_PATH     = "$env:USERPROFILE\.wangbo-brain"
$MEMORY_SRC     = "$env:USERPROFILE\.claude\projects\D--AI-Workspaces\memory"
$MEMORY_DST     = "$BRAIN_PATH\memory\claude-code"
$LOG_FILE       = "$env:USERPROFILE\.claude\skills-sync.log"

# ── 编码修复（避免日志乱码）──────────────────────────────────────────────────
[Console]::OutputEncoding    = [System.Text.Encoding]::UTF8
$OutputEncoding              = [System.Text.Encoding]::UTF8

function Log {
    param([string]$msg)
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
    Write-Host $line
    $line | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
}

function Run-Git {
    # 静默运行 git，把 stderr（红色进度）重定向，只在真正失败时报错
    param([string[]]$args)
    $result = & git @args 2>&1
    return ($result -join "`n")
}

# ── 1. PUSH Skills: ~/.claude/skills → GitHub ────────────────────────────────
function Push-Skills {
    Log "=== PUSH: Skills → GitHub (bog5d/claude-skills) ==="
    Set-Location $CLAUDE_SKILLS
    Run-Git "add", "-A" | Out-Null
    $changed = (Run-Git "diff", "--cached", "--name-only").Trim()
    if ($changed) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        Run-Git "commit", "-m", "auto-sync: $stamp" | Out-Null
        $pushResult = Run-Git "push", "origin", "master"
        $count = ($changed -split "`n" | Where-Object { $_ }).Count
        Log "推送成功: $count 个文件变更"
    } else {
        Log "Skills 无变更，跳过推送"
    }
}

# ── 2. PULL Skills: GitHub → ~/.claude/skills ────────────────────────────────
function Pull-Skills {
    Log "=== PULL: GitHub → Skills ==="
    Set-Location $CLAUDE_SKILLS
    $result = Run-Git "pull", "origin", "master"
    if ($result -match "Already up to date") {
        Log "Skills 已是最新"
    } else {
        Log "Skills 已更新: $($result -replace '\n',' ')"
    }
}

# ── 3. SYNC Skills: ~/.claude/skills → ~/.cursor/skills ──────────────────────
function Sync-ToCursor {
    Log "=== SYNC: Skills → Cursor ==="
    if (-not (Test-Path $CURSOR_SKILLS)) {
        New-Item -ItemType Directory -Path $CURSOR_SKILLS -Force | Out-Null
    }
    Get-ChildItem $CLAUDE_SKILLS -Directory | Where-Object { $_.Name -notmatch "^\." } | ForEach-Object {
        $skillMd = Join-Path $_.FullName "SKILL.md"
        if (-not (Test-Path $skillMd)) { return }
        $dst = Join-Path $CURSOR_SKILLS $_.Name
        if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst -Force | Out-Null }
        Get-ChildItem $_.FullName -File -Recurse | Where-Object {
            $_.Length -lt 512000 -and
            $_.Extension -notin @(".png",".jpg",".jpeg",".gif",".webp",".mp4",".zip",".exe")
        } | ForEach-Object {
            $rel = $_.FullName.Substring($_.FullName.IndexOf($_.DirectoryName.Replace($CLAUDE_SKILLS + "\" + (Split-Path $_.FullName -Parent | Split-Path -Leaf), "").TrimStart("\")))
            $dstFile = Join-Path $dst ($_.FullName.Substring((Join-Path $CLAUDE_SKILLS $_.DirectoryName.Replace($CLAUDE_SKILLS,"").TrimStart("\")).Length + 1) )
            $dstFile = Join-Path $dst $_.Name   # 简化：只同步顶层文件
            Copy-Item $_.FullName $dstFile -Force
        }
        Log "  → Cursor: $($_.Name)"
    }
}

# ── 4. MEMORY: ~/.claude/.../memory → ~/.wangbo-brain → GitHub ───────────────
function Sync-Memory {
    Log "=== MEMORY: Claude → Brain → GitHub (bog5d/wangbo-brain) ==="

    # 确认 brain 仓库存在
    if (-not (Test-Path "$BRAIN_PATH\.git")) {
        Log "Brain 仓库不存在，正在 clone..."
        Run-Git "clone", "https://github.com/bog5d/wangbo-brain.git", $BRAIN_PATH | Out-Null
    }

    # 先 pull（防止冲突）
    Set-Location $BRAIN_PATH
    $pullResult = Run-Git "pull", "origin", "master"
    if ($pullResult -notmatch "Already up to date") {
        Log "Brain 已从 GitHub 更新"
    }

    # 把记忆文件复制到 brain/memory/claude-code/
    if (Test-Path $MEMORY_SRC) {
        if (-not (Test-Path $MEMORY_DST)) {
            New-Item -ItemType Directory -Path $MEMORY_DST -Force | Out-Null
        }
        Copy-Item "$MEMORY_SRC\*" $MEMORY_DST -Force -Recurse
        Log "记忆文件已复制到 Brain"
    } else {
        Log "⚠️  记忆源路径不存在: $MEMORY_SRC"
    }

    # push brain 到 GitHub
    Set-Location $BRAIN_PATH
    Run-Git "add", "-A" | Out-Null
    $changed = (Run-Git "diff", "--cached", "--name-only").Trim()
    if ($changed) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        Run-Git "commit", "-m", "memory-sync: $stamp" | Out-Null
        Run-Git "push", "origin", "master" | Out-Null
        $count = ($changed -split "`n" | Where-Object { $_ }).Count
        Log "记忆推送成功: $count 个文件"
    } else {
        Log "记忆无变更，跳过推送"
    }
}

# ── 5. STATUS ─────────────────────────────────────────────────────────────────
function Show-Status {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Set-Location $CLAUDE_SKILLS

    $skillCount  = (Get-ChildItem $CLAUDE_SKILLS -Recurse -Filter "SKILL.md" | Measure-Object).Count
    $topSkills   = Get-ChildItem $CLAUDE_SKILLS -Directory | Where-Object { $_.Name -notmatch "^\." }
    $lastCommit  = Run-Git "log", "--oneline", "-1"
    $lastTime    = Run-Git "log", "-1", "--format=%ci"

    Write-Host ""
    Write-Host "════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "   🧠 wangbo AI Brain — 同步状态" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [Skills 库] bog5d/claude-skills（公开）" -ForegroundColor Yellow
    Write-Host "  Skills 数量 : $skillCount 个 SKILL.md" -ForegroundColor Green
    Write-Host "  最后同步    : $lastTime" -ForegroundColor Green
    Write-Host "  最新 commit : $lastCommit" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Skills 列表：" -ForegroundColor White
    $topSkills | ForEach-Object {
        $sub = (Get-ChildItem $_.FullName -Recurse -Filter "SKILL.md" | Measure-Object).Count
        $label = if ($sub -gt 1) { "  + $($_.Name)  ($sub sub-skills)" } else { "  + $($_.Name)" }
        Write-Host $label -ForegroundColor Gray
    }

    Write-Host ""
    Write-Host "  [Memory 库] bog5d/wangbo-brain（私有）" -ForegroundColor Yellow
    if (Test-Path $BRAIN_PATH) {
        Set-Location $BRAIN_PATH
        $memFiles   = (Get-ChildItem "$BRAIN_PATH\memory\claude-code" -File -ErrorAction SilentlyContinue | Measure-Object).Count
        $brainCommit = Run-Git "log", "--oneline", "-1"
        Write-Host "  记忆文件数  : $memFiles 个" -ForegroundColor Green
        Write-Host "  最新 commit : $brainCommit" -ForegroundColor DarkGray
    } else {
        Write-Host "  Brain 仓库未 clone（运行 auto 模式自动初始化）" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "  [Cursor 同步]" -ForegroundColor Yellow
    if (Test-Path $CURSOR_SKILLS) {
        $cursorCount = (Get-ChildItem $CURSOR_SKILLS -Directory | Measure-Object).Count
        Write-Host "  ~/.cursor/skills/ ($cursorCount 个 packages)" -ForegroundColor Green
    } else {
        Write-Host "  未同步" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "  [最近同步事件]" -ForegroundColor Yellow
    if (Test-Path $LOG_FILE) {
        Get-Content $LOG_FILE | Where-Object { $_ -match "===" } | Select-Object -Last 6 |
            ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
    }
    Write-Host ""
    Write-Host "════════════════════════════════════════════" -ForegroundColor Cyan
}

# ── 主流程 ────────────────────────────────────────────────────────────────────
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
        Log "=== 全部同步完成（Skills + Memory）==="
    }
    default  { Write-Host "用法: .\sync-skills.ps1 [auto|push|pull|sync|memory|status]" }
}
