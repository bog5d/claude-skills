---
name: cross-profile-skills-sync
description: 为多个 Hermes profile 设置 skills 双向自动同步——每 N 分钟比较 mtime，较新的覆盖旧的，新 skill 自动拷贝，永不删除。
triggers:
  - "profile skills sync"
  - "跨 profile 同步 skills"
  - "两个 profile 互相学习"
  - "skills 双向同步"
---

# 跨 Profile Skills 双向同步

## 场景

用户有多个 Hermes profile（`default` 和 `her-m2`），每个 profile 有独立的 `skills/` 目录。希望所有 profile 的 skills 自动互相学习，且增量推送到 GitHub 供跨 AI 工具使用。

**四端同步路径（波总环境）：**
- SRC1: `~/.hermes/skills/` （当前 active profile her-m2）
- SRC2: `~/.hermes/profiles/her-m2/skills/` （her-m2 profile 冗余副本）
- SRC3: `~/.hermes/skills/` （default profile 的技能目录 — HERMES_HOME=/Users/mac/.hermes 从 launchd plist 解析）
- SRC4: `~/.hermes/profiles/english-tutor/skills/` （@Engcjd_bot 英语伴学 profile）

## 步骤

### 1. 创建三端同步脚本

脚本位置: `~/.hermes/scripts/sync_skills_cross_profile.sh`

**三阶段架构：**
- Phase 1: Tysk pull — 从 GitHub 拉最新 claude-skills + wangbo-brain
- Phase 2: 三端 mtime 比对 — 找最新版本，覆盖所有滞后端
- Phase 3: Tysk push — 本地 skills → rsync 进 claude-skills repo → git push GitHub

Phase 2 核心逻辑（三端比对）：
- 遍历四个目录的所有 SKILL.md
- 比较 mtime，找 newest（最晚修改的作为权威源）
- newest → 覆盖其余两端的旧版本
- 不删除任何 skill，只增加和更新
- **rsync 必须排除凭证文件**（`.env.local`, `.env`, `*.secret`, `*.pem`, `*.p12`, `*.pfx`）— 这些文件从不在同步范围中

### 2. GitHub Push 关键配置

**⚠️ HTTPS push 必挂：** 大 repo（32MB, 468文件）用普通 HTTPS URL push 必超时。必须用 Token 认证 URL：
```bash
git remote set-url origin https://<token>@github.com/bog5d/claude-skills.git
```
SSH 未配置时此方案是唯一可行路径。

### 3. 首次运行验证

```bash
bash ~/.hermes/scripts/sync_skills_cross_profile.sh
# 确认三端数量一致
echo "her-m2: $(find ~/.hermes/skills -name SKILL.md -not -path '*/.git/*' | wc -l)"
echo "her-m2 profile: $(find ~/.hermes/profiles/her-m2/skills -name SKILL.md -not -path '*/.git/*' | wc -l)"
echo "default: $(find ~/.hermes/hermes-agent/skills -name SKILL.md -not -path '*/.git/*' | wc -l)"
echo "english-tutor: $(find ~/.hermes/profiles/english-tutor/skills -name SKILL.md -not -path '*/.git/*' | wc -l)"
```

### 4. 挂 cron job

```bash
cronjob create \
  --name "skills-sync-四端" \
  --schedule "every 30m" \
  --prompt "Execute bash ~/.hermes/scripts/sync_skills_cross_profile.sh. Report results." \
  --deliver local
```
⚠️ `deliver=local` 关键——避免每 30 分钟往 Telegram 推送同步日志。

### 5. Pre-Commit Secret Scan（push 前必须执行）

**铁律：任何 commit 前必须扫描敏感文件。** 公开仓库（claude-skills）一旦含真实密钥，GitHub Push Protection 会静默拒绝 push，且 `2>/dev/null` 吞掉错误，导致未推送提交堆积。

```bash
# 扫描暂存区和未跟踪文件中的常见密钥模式
cd /Users/mac/.claude/skills
git diff --cached --diff-filter=ACMR -S '' -- '*.env*' '*.secret*' '*.key' '*.pem' '*.p12' '*.pfx' 2>/dev/null
# 更通用的：扫描所有新增/修改文件中的常见密钥模式
git diff --cached -- '*.env*' '*.local' '*.secret' '*.key' '*.pem' '*.p12' '*.pfx' '*.yml' '*.yaml' '*.json' 2>/dev/null | grep -iE '(api[_-]?key|secret|token|password|credential|PRIVATE.*KEY|DEEPSEEK|WECHAT.*SECRET|GH_|github_pat_|sk-[A-Za-z0-9]{20})'
```

**如果扫描发现密钥：**
1. 不要 commit — 直接从暂存区移除：`git reset <file>`
2. 确保 `.gitignore` 包含 `*.env.local`、`*.env`、`*.secret`
3. 重新 commit 只包含安全变更

### 6. Post-Sync 验证（每次 cron 运行后必须执行）

脚本 `2>/dev/null` 会吞掉 push 错误，即使 GitHub push protection 拒绝了全部提交，脚本仍返回 `EXIT:0`。**每次 cron 运行后必须检查：**

```bash
# 检查是否有未推送的提交（> 0 说明 push 被静默阻止）
cd /Users/mac/.claude/skills && git log --oneline origin/master..HEAD | wc -l
```

如果 > 0，立即执行 token-scrub 修复流程（见下方「GitHub Push Protection 会静默阻止含 token 的 push」）。

## 实战教训

### ⚠️ Git identity 未配置导致 push 失败
如果 git 的 user.name/user.email 为空，某些 git push 操作可能被阻止（第一次 push 会使用系统默认 identity 成功，但后续可能卡住）。修复：
```bash
cd ~/.claude/skills && git config user.name "Hermes Agent" && git config user.email "hermes@nousresearch.com"
cd ~/.wangbo-brain && git config user.name "Hermes Agent" && git config user.email "hermes@nousresearch.com"
```
**根因：** 原脚本只有 Phase 1(Pull) + Phase 2(本地同步)，缺 Phase 3(Push)。另外 HTTPS push 在 32MB repo 上必定超时，需 Token URL。

**修复后验证：**
```bash
curl -s "https://api.github.com/repos/bog5d/claude-skills/commits/master" | python3 -c "import sys,json; print(json.load(sys.stdin)['commit']['message'][:80])"
```

### ⚠️ 致命：$HOME 在 Hermes 运行时被重写
Hermes Agent 在 gateway/terminal 运行时会修改 `$HOME` 指向 profile 目录（如 `/Users/mac/.hermes/profiles/her-m2/home/`），导致脚本中所有 `$HOME/...` 路径解析错误（形成双重嵌套路径）。
**修复方案：** 所有路径必须硬编码为绝对路径 `/Users/mac/...`，禁止使用 `$HOME`。

### ⚠️ default profile 路径特殊
default profile 的 skills 不在 `~/.hermes/profiles/default/skills/`，而在 `~/.hermes/skills/`（因为 launchd plist 中 `HERMES_HOME=/Users/mac/.hermes`）。

### ⚠️ rsync --delete 会删 GitHub 仓库根文档
Phase 3 的 `rsync -a --delete "$SRC1/" ./` 会将仓库根目录所有不在 SRC1 里的文件删除——包括 README.md、AGENTS.md、SKILLS_SYNC_GUIDE.md。必须加 exclude：
```bash
rsync -a --delete --exclude='.git' --exclude='README.md' --exclude='AGENTS.md' --exclude='SKILLS_SYNC_GUIDE.md' "$SRC1/" ./
```

### ⚠️ rsync 不传 `--exclude='.git'` 会误删 .git 目录
如果从 non-git 源 rsync 到 git repo 目标，不加 `--exclude='.git'` 会删除目标的 .git 目录，后续 git push 无法工作。

### ⚠️ GitHub Push Protection 会静默阻止含 token 的 push
如果任何 skill 文件包含真实的 GitHub PAT（如 `ghp_...` 或 `github_pat_...`），GitHub push protection 会拒绝整个 push，且脚本的 `2>/dev/null` 会吞掉错误信息，导致**静默堆积未推送提交**（本次经历了 14 commits / 12+ 小时的黑洞）。

**检测方法：**
```bash
cd /Users/mac/.claude/skills && git log --oneline origin/master..HEAD | wc -l
# 如果 > 0，说明有未推送的提交
```

**根因定位：** 去掉 `2>/dev/null` 直接 push 看 GitHub 返回的具体错误：
```bash
cd /Users/mac/.claude/skills && git push origin master 2>&1
# 会列出含 token 的文件路径和行号
```

**修复流程（详见 references/token-scrub-procedure.md）：**
1. 用 GitHub 返回的路径定位所有 token
2. 全部替换为占位符 `ghp_YOUR_TOKEN_HERE`
3. Squash 所有未推送提交为单提交：`git reset --soft origin/master && git commit -m "..." && git push`
4. 同步回 Hermes profile 源文件

**预防：** 新 skill 或模板中嵌入的代码示例，token 必须用占位符，绝不能放真实凭证。

### ⚠️ token-scrub-procedure.md 自身可能携带真实 token（递归问题）

**现象：** 就连教人如何清洗 token 的参考文件 `references/token-scrub-procedure.md` 自身也可能含有真实 token（前人在示例中误用了真实凭证）。当你按 GitHub Push Protection 错误信息追踪到该文件时，会发现文件本身也是"污染源"。

**检测：** 去掉 `2>/dev/null` 直接 push，GitHub 会返回含 token 的文件路径和行号：
```bash
cd /Users/mac/.claude/skills && git push origin master 2>&1
# 输出会列出所有违规文件路径和行号，包括 references/token-scrub-procedure.md
```

**修复：**
1. 用 `git show HEAD:path > /tmp/file && sed -n 'Np' /tmp/file | xxd` 提取真实 token（`read_file` 会掩码）
2. 用 `patch` 工具替换所有真实 token 为 `ghp_YOUR_TOKEN_HERE`（`replace_all: true`）
3. 用 `git commit --amend --no-edit` 修正当前提交（如果只有一个未推送提交）
4. `git push origin master` 重新推送
5. 将清洗后的文件复制回 Hermes 源目录，防止下次同步复现：
   ```bash
   cp /Users/mac/.claude/skills/path/to/file.md /Users/mac/.hermes/profiles/her-m2/skills/path/to/file.md
   ```

**根因：** 有人在该参考文件中用真实的 GitHub PAT 作为示例文本，违反了"示例中 token 必须用占位符"的铁律。该文件虽然是教人洗 token 的，但自身违反了规则。

### ⚠️ .env.local / .env 等凭证文件会被 rsync 进 git 仓库

**现象：** 同步脚本 Phase 2 的 `rsync -a` 会把源目录中所有文件（包括 `.env.local`、`.env` 等含 API key 的配置文件）复制到 GitHub 仓库目录，导致 `git add -A` 或 `git commit` 将它们纳入版本控制。GitHub Push Protection 检测到真实密钥后会拒绝 push，且 `2>/dev/null` 吞掉错误，造成静默堆积。

**本次案例：** `social-media/wechat-publish-direct/.env.local` 包含 DeepSeek API Key 和 WeChat App Secret，被 rsync 进 `.claude/skills/` 后提交，push 被拒。

**修复流程：**
1. 从 git 跟踪中移除：`git rm --cached <path-to-env-file>`
2. 只提交非敏感变更：`git add -A` 之前先确认哪些文件被标记，或用 `git add <safe-file-1> <safe-file-2>` 精确指定
3. 重新 commit：`git commit -m '...'`
4. 推送：`git push origin master`
5. 在仓库根目录添加 `.gitignore` 防止复发：
   ```bash
   echo -e '.env.local\n.env\n*.secret' >> .gitignore
   git add .gitignore && git commit -m 'chore: add .gitignore' && git push
   ```

**预防：** 同步脚本的 rsync 阶段应排除 `.env*`、`.local` 等凭证文件，或在 `.claude/skills/.gitignore` 中始终维护这些排除项。

### ⚠️ Cron job 会把 .env.local 重新同步进 git 仓库

**现象：** 即使你在 git 仓库中清除了 `.env.local`，cron 定时任务每 30 分钟运行一次 `sync_skills_cross_profile.sh`，rsync 会从源 profile 目录重新把它拉回仓库，再次触发 GitHub Push Protection 拒绝。

**根本原因：** rsync 的源目录（各 profile 的 `skills/`）中包含 `.env.local`，rsync -a 会复制所有文件。

**修复方案（铁律）：** Phase 2 的 rsync 命令必须在源端就排除凭证文件：
```bash
# 错误写法
rsync -a --delete "$SRC1/" "$DEST/"

# 正确写法 — 在 rsync 源端排除 .env* 和凭证文件
rsync -a --delete \
  --exclude='.env.local' \
  --exclude='.env' \
  --exclude='*.secret' \
  --exclude='*.pem' \
  --exclude='*.p12' \
  --exclude='*.pfx' \
  --exclude='.DS_Store' \
  "$SRC1/" "$DEST/"
```

**额外防护：** 如果 cron 已经在运行，手动删除所有源 profile 中的 `.env.local`：
```bash
find /Users/mac/.hermes/profiles/*/skills -name '.env.local' -delete
find /Users/mac/.hermes/skills -name '.env.local' -delete
```

### ⚠️ .env.local 被 commit 后：`git rm --cached` 不够，必须 `filter-branch`

**现象：** `git rm --cached <file>` 只从当前工作树解除跟踪，**不会**清除历史中已存在的提交。如果密钥已经出现在历史中的某个提交，GitHub Push Protection 仍然会拒绝 push。

**正确修复：** 使用 `git filter-branch` 从所有历史中移除：
```bash
cd /Users/mac/.claude/skills
git filter-branch -f --index-filter 'git rm --cached --ignore-unmatch social-media/wechat-publish-direct/.env.local' HEAD
git for-each-ref --format='%(refname)' refs/original/ | xargs -n 1 git update-ref -d
git gc --prune=now
# 确认干净后 force push
git push origin master --force
```

**铁律：** 公开仓库含密钥 → 永远用 `filter-branch` 或 `git rebase -i` 重写历史。`--amend` 只对单个提交有效。

## 限制

- 只在同一台机器上的 profile 间同步
- 不跨机器、不跨设备
- 跨设备同步通过 GitHub 仓库中转（Tysk 协议）
- HTTPS push 需要 Token URL，SSH 需提前配置好

## 支持文件

- `templates/pre-commit-secret-scan.sh` — pre-commit hook，自动扫描暂存文件中的密钥模式（api_key, secret, token, DEEPSEEK_API_KEY, WECHAT_APP_SECRET 等）。复制到 `.git/hooks/pre-commit` 自动拦截含密钥的提交。
- `references/token-scrub-procedure.md` — 清理历史中泄露 token 的完整流程（filter-branch + force push）。
- `templates/gitignore-credentials.txt` — 用于 claude-skills 仓库的 .gitignore 模板，排除 .env 等凭证文件。
