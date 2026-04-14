# sync-skills.ps1
# 统一 Skills 同步脚本 - 单一真相源 (GitHub) → 所有 AI 工具
# 
# 功能：
#   1. push: 将 ~/.claude/skills/ 的变更推送到 GitHub
#   2. pull: 从 GitHub 拉取最新 → 同步到 ~/.cursor/skills/
#   3. auto: push + pull + sync (计划任务默认模式)
#
# 用法:
#   .\sync-skills.ps1             # 默认 auto 模式
#   .\sync-skills.ps1 push        # 只推送
#   .\sync-skills.ps1 pull        # 只拉取并同步到 Cursor
#   .\sync-skills.ps1 status      # 查看状态

param(
    [string]$Mode = "auto"
)

$CLAUDE_SKILLS = "$env:USERPROFILE\.claude\skills"
$CURSOR_SKILLS = "$env:USERPROFILE\.cursor\skills"
$LOG_FILE      = "$env:USERPROFILE\.claude\skills-sync.log"
$TIMESTAMP     = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Log {
    param([string]$msg)
    $line = "[$TIMESTAMP] $msg"
    Write-Host $line
    Add-Content -Path $LOG_FILE -Value $line -ErrorAction SilentlyContinue
}

# ── 1. PUSH: claude/skills → GitHub ─────────────────────────────────────────
function Push-Skills {
    Log "=== PUSH: ~/.claude/skills → GitHub ==="
    Set-Location $CLAUDE_SKILLS
    
    git add -A
    $diff = git diff --cached --name-only 2>$null
    if ($diff) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        git commit -m "auto-sync: $stamp" 2>$null
        git push origin master 2>$null
        Log "推送成功: $($diff.Count) 个文件变更"
    } else {
        Log "无变更，跳过推送"
    }
}

# ── 2. PULL: GitHub → ~/.claude/skills ──────────────────────────────────────
function Pull-Skills {
    Log "=== PULL: GitHub → ~/.claude/skills ==="
    Set-Location $CLAUDE_SKILLS
    $result = git pull origin master 2>&1
    Log "git pull: $result"
}

# ── 3. SYNC: ~/.claude/skills → ~/.cursor/skills ─────────────────────────────
function Sync-ToCursor {
    Log "=== SYNC: ~/.claude/skills → ~/.cursor/skills ==="
    
    if (-not (Test-Path $CURSOR_SKILLS)) {
        New-Item -ItemType Directory -Path $CURSOR_SKILLS -Force | Out-Null
        Log "创建目录: $CURSOR_SKILLS"
    }

    # 遍历 claude/skills 下的每个 skill 目录
    Get-ChildItem $CLAUDE_SKILLS -Directory | Where-Object { $_.Name -notmatch "^\.git" } | ForEach-Object {
        $skillName = $_.Name
        $srcSkillDir = $_.FullName
        $dstSkillDir = Join-Path $CURSOR_SKILLS $skillName
        
        # 只同步包含 SKILL.md 的目录
        $skillMd = Join-Path $srcSkillDir "SKILL.md"
        if (-not (Test-Path $skillMd)) { return }

        if (-not (Test-Path $dstSkillDir)) {
            New-Item -ItemType Directory -Path $dstSkillDir -Force | Out-Null
        }

        # 复制 SKILL.md 和其他文本文件（跳过大型二进制文件 >500KB）
        Get-ChildItem $srcSkillDir -File -Recurse | Where-Object {
            $_.Length -lt 512000 -and
            $_.Extension -notin @(".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".zip", ".exe")
        } | ForEach-Object {
            $relPath = $_.FullName.Substring($srcSkillDir.Length + 1)
            $dstFile  = Join-Path $dstSkillDir $relPath
            $dstDir   = Split-Path $dstFile -Parent
            if (-not (Test-Path $dstDir)) {
                New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
            }
            Copy-Item $_.FullName $dstFile -Force
        }
        Log "  同步: $skillName → Cursor"
    }
}

# ── 4. STATUS ────────────────────────────────────────────────────────────────
function Show-Status {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

    Set-Location $CLAUDE_SKILLS
    $lastCommit = git log --oneline -1 2>$null
    $lastCommitTime = git log -1 --format="%ci" 2>$null

    # 统计 skills：每个含 SKILL.md 的目录算一个 skill
    $allSkillDirs = Get-ChildItem $CLAUDE_SKILLS -Recurse -Filter "SKILL.md" |
        Select-Object -ExpandProperty DirectoryName | Sort-Object -Unique
    $topSkills = Get-ChildItem $CLAUDE_SKILLS -Directory | Where-Object { $_.Name -notmatch "^\." -and $_.Name -ne ".git" }

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "   Skills Library Dashboard" -ForegroundColor Cyan
    Write-Host "   https://github.com/bog5d/claude-skills" -ForegroundColor DarkCyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Top-level skill packages : $($topSkills.Count)" -ForegroundColor Green
    Write-Host "  Total SKILL.md files     : $($allSkillDirs.Count)" -ForegroundColor Green
    Write-Host "  Last sync to GitHub      : $lastCommitTime" -ForegroundColor Green
    Write-Host "  Latest commit            : $lastCommit" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "  [Skill Packages]" -ForegroundColor Yellow
    $topSkills | ForEach-Object {
        $name = $_.Name
        # 统计该 package 内的 sub-skills
        $subCount = (Get-ChildItem $_.FullName -Recurse -Filter "SKILL.md" | Measure-Object).Count
        if ($subCount -le 1) {
            Write-Host "    + $name" -ForegroundColor White
        } else {
            Write-Host "    + $name  ($subCount sub-skills inside)" -ForegroundColor White
        }
    }

    Write-Host ""
    Write-Host "  [Cursor sync]" -ForegroundColor Yellow
    if (Test-Path $CURSOR_SKILLS) {
        $cursorCount = (Get-ChildItem $CURSOR_SKILLS -Directory | Measure-Object).Count
        Write-Host "    ~/.cursor/skills/  ($cursorCount packages synced)" -ForegroundColor White
    } else {
        Write-Host "    Not synced yet  (run: .\sync-skills.ps1 pull)" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "  [Last 5 sync events]" -ForegroundColor Yellow
    if (Test-Path $LOG_FILE) {
        Get-Content $LOG_FILE | Where-Object { $_ -match "===" } | Select-Object -Last 5 |
            ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
    }
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
}

# ── 主流程 ───────────────────────────────────────────────────────────────────
switch ($Mode.ToLower()) {
    "push"   { Push-Skills }
    "pull"   { Pull-Skills; Sync-ToCursor }
    "sync"   { Sync-ToCursor }
    "status" { Show-Status }
    "auto"   {
        Push-Skills
        Pull-Skills
        Sync-ToCursor
        Log "=== 同步完成 ==="
    }
    default {
        Write-Host "用法: .\sync-skills.ps1 [auto|push|pull|sync|status]"
    }
}
