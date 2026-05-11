# FOS 外发版标准流程

**触发**：用户输入 `/release-fos` 或说"打外发包"/"发版"

**执行前宣告**：「我在用 release-fos skill 执行标准发版流程。」

---

## 核心原则（每次发版前默念）

- **包里只放同事真正需要的** — 没有 tests/、docs/、node_modules、.env
- **zip 永远落在 `D:\Releases\`** — 不落根目录、不落桌面
- **包里必有 `本次更新说明.md`** — 同事打开 zip 第一眼就知道这版改了什么、怎么测
- **每次发版必须过测试** — 测试不过不发包

---

## 发版检查清单（必须按顺序，每步完成后在脑内打勾）

### 阶段 1 — 代码验证

- [ ] 确认当前在 `D:\AI_Workspaces\CangJie_FOS\backend\` 目录
- [ ] 运行全套测试：`uv run --extra dev pytest tests/ --ignore=tests/test_doctor_script.py -q`
  - 必须 **全部 passed，0 failed**
  - 记录通过数，填入后续 CHANGELOG 条目
- [ ] 确认前端已构建：`cd frontend && npm run build`
  - 必须 **0 errors**（warnings 可忽略）

### 阶段 2 — 更新文档（三份，缺一不可）

#### 2a. CHANGELOG.md（面向开发/AI）
- 在 `## [Unreleased]` 下方添加新的版本块：
  ```
  ## [X.Y.Z] — YYYY-MM-DD  Phase X.X 名称
  ### Added
  - 功能描述（说清楚文件路径和行为变化）
  ### Changed
  - 测试基线：N → M passed（+delta）
  ```
- 版本号格式：major.minor.patch（路演情报这类新功能 = minor+1，bugfix = patch+1）

#### 2b. packaging/本次更新说明.md（面向同事，进 zip 根目录）
- 更新顶部的**版本号和日期**
- **新增了什么** — 用同事能懂的语言，不写技术细节
- **怎么用** — 写具体操作步骤（点哪里、填什么、等多久）
- **怎么测** — 验收清单，能勾能划，通了就是通了
- 不超过 2 屏，宁可少不要多

#### 2c. 同事上手指南.md（面向新同事，在 CangJie_FOS/ 里）
- 如有新功能，在第三节「系统现有功能一览」里增加描述
- 如有新测试场景，在第四节「怎么测试」里加验收项
- 更新底部版本号和日期

### 阶段 3 — 打包

运行打包脚本（固定落在 `D:\Releases\`，不需要加参数）：
```powershell
cd D:\AI_Workspaces\CangJie_FOS
.\tools\build_release_zip.ps1
```

**验证输出：**
- [ ] 看到 `==== Release OK ====`
- [ ] 文件在 `D:\Releases\CangJie_FOS_Release_YYYYMMDD_HHMMSS.zip`
- [ ] 大小合理（通常 2~5 MB，超过 20MB 说明有文件没排除）

**快速验包**（可选但推荐）：
```powershell
# 列出 zip 根目录文件，确认有 bat 文件和本次更新说明.md
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::OpenRead("D:\Releases\刚才生成的.zip").Entries |
  Where-Object { $_.FullName -notmatch "/" } |
  Select-Object FullName, Length
```
根目录应有：`点击开始-仓颉FOS.bat`、`00_先看这一行.txt`、`本次更新说明.md`、`仓颉FOS-使用指引...md`

### 阶段 4 — Git 提交

```bash
git add CHANGELOG.md packaging/本次更新说明.md 同事上手指南.md
git commit -m "release: vX.Y.Z + 更新发版文档"
git push origin master
```

### 阶段 5 — 发版报告

向用户报告（格式如下）：

```
✅ 外发版已完成

版本：X.Y.Z（YYYY-MM-DD）
文件：D:\Releases\CangJie_FOS_Release_YYYYMMDD_HHMMSS.zip
大小：X.X MB
SHA256：XXXX...
测试：NNN passed

包内容：
  ✓ 点击开始-仓颉FOS.bat（双击直接启动）
  ✓ 本次更新说明.md（根目录，同事首看）
  ✓ CangJie_FOS/（后端+前端，无 tests/docs/node_modules）
  ✓ AI_Pitch_Coach/（分析引擎）
  ✓ .fos_data/（占位桥接目录）
```

---

## 外发包内容标准（红线，不能破）

### 必须在包里
| 文件 | 位置 | 说明 |
|------|------|------|
| `点击开始-仓颉FOS.bat` | 根目录 | 新同事唯一需要点的入口 |
| `00_先看这一行.txt` | 根目录 | 3行说明，纯文本，打开即读 |
| `本次更新说明.md` | 根目录 | 每次发版更新 |
| `仓颉FOS-使用指引...md` | 根目录 | 详细上手指南（通用，不需每版改） |
| `CangJie_FOS/backend/` | 子目录 | 后端代码 |
| `CangJie_FOS/frontend/dist/` | 子目录 | 预编译前端 |
| `CangJie_FOS/填写API密钥_双击我.bat` | 子目录 | Key 配置入口 |
| `CangJie_FOS/诊断_打不开请运行我.bat` | 子目录 | 排障入口 |
| `AI_Pitch_Coach/src/` | 子目录 | 分析引擎（无此目录豆豆报错） |
| `.fos_data/` | 根目录 | 空占位目录，首次启动后自动填充 |

### 绝对不能在包里
| 文件/目录 | 原因 |
|-----------|------|
| `.env` | API Key 泄露 |
| `tests/` | 无用，且体积大 |
| `docs/` | 内部规划文档，外发无意义 |
| `node_modules/` | 体积巨大（几百MB） |
| `.venv/` | 虚拟环境，体积巨大 |
| `CLAUDE.md` / `AGENTS.md` | AI内部指令，不相关 |
| `TODO_LIST_*.md` | 内部规划 |
| `*.zip` | 防止老包嵌套进新包 |
| `data/audio/` | 用户音频，隐私 |
| `data/html_reports/` | 生成的报告，非代码 |

---

## 版本号规则

```
vA.B.C
A（major）= 架构性重大变更（目前保持 0）
B（minor）= 新功能上线（+1）
C（patch）= bug 修复、文档更新（+1）
```

每次发版 commit message 格式：
```
release: vX.Y.Z — 一句话说明主要变化

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

---

## 紧急发版（hotfix，不做新功能）

1. 跳过阶段 2c（同事上手指南），只改 CHANGELOG + 本次更新说明
2. `本次更新说明.md` 简写：「**紧急修复**：描述修了什么，其余功能不变」
3. 版本号 patch +1（例如 0.4.1 → 0.4.2）
4. 测试只跑相关模块，不跑全套（节约时间），但必须通过

---

## 常见遗漏提醒

- **packaging/本次更新说明.md 忘记更新** → 同事打开 zip 看到的还是上个版本的说明
- **OutDir 没有用 D:\Releases** → zip 落在项目根目录，和代码混在一起
- **前端没有重新 build** → dist/ 是旧版，功能对不上
- **CHANGELOG 版本块写在 Unreleased 里没提升** → 版本号乱掉
