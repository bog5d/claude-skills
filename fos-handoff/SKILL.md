# fos-handoff — FOS 开发会话交接 Skill

**触发词**：`/fos-handoff`、「生成交接文档」、「帮我写交接」、「下一个 AI 怎么接」、「会话结束了总结一下」

**执行前宣告**：「我在用 fos-handoff skill，生成接力开发交接包。」

---

## ⚠️ 铁律：以下情况必须自动触发，无需用户手动说

| 触发时机 | 说明 |
|---------|------|
| `git push origin master` 执行完毕 | 无论是普通开发还是发版，push 完必须执行 |
| `release-fos` skill 的阶段 4.5 | 发版流程内置调用，不另行提醒 |
| 上下文接近满载，准备开新会话 | AI 自判断，主动提示用户确认后执行 |

**不允许**："push 完了，交接文档下次再说" — 没有下次，只有现在。

---

## 这个 Skill 做什么

开发会话结束时，自动把「这一轮做了什么、改了哪些文件、还剩什么」整理成两份东西：

1. **更新 CLAUDE.md 的「改动文件清单」节** — 让仓库本身就是最新的交接文档
2. **输出一段「直接粘给下一个 AI」的交接 Prompt** — 新 AI 粘贴即用，不需要再解释背景

---

## 执行流程

### 第1步：收集当前状态

```bash
# 跑测试，拿最新基线
cd backend && uv run --extra dev pytest tests/ --ignore=tests/test_doctor_script.py -q 2>&1 | tail -3

# 看本次会话改了哪些文件
git diff --name-only HEAD~5..HEAD   # 最近5个commit的改动文件

# 看最近commit列表
git log --oneline -8
```

记录：
- 当前测试通过数（如：502 passed）
- 本次会话涉及的文件列表
- 最新 commit hash

---

### 第2步：更新 CLAUDE.md

打开 `CLAUDE.md`，更新以下内容（不要删，只更新/追加）：

**接手速览头部**：
```
> 最后更新：YYYY-MM-DD | 当前版本：vX.Y.Z | 测试基线：NNN passed | 单仓库可运行：✅
```

**「最近做了什么」版本历史表**：追加本次版本行。

**「改动文件清单」节**：按 Bug/功能分组，每个文件写一行「改了什么」。格式：

```markdown
### vX.Y.Z 改动文件清单（YYYY-MM-DD）

| 文件 | 改了什么 |
|------|---------|
| `backend/src/...` | 一句话说明 |
| `frontend/src/...` | 一句话说明 |
```

**「待处理问题」**：更新剩余未解决问题，并标注「下一版从哪里入手」。

---

### 第3步：输出「直接粘给下一个 AI」的交接 Prompt

输出格式固定如下，一段 Markdown，可以直接复制粘贴：

```markdown
---
## 仓颉 FOS — 接手说明（vX.Y.Z，YYYY-MM-DD）

你即将接手「仓颉 FOS」项目。读这段话，覆盖你从仓库老文档里读到的任何过期信息。

### 最重要的纠正
[列出任何老文档里有的、现在已经过时的描述，例如：「不再需要 AI_Pitch_Coach 外部依赖」]

### 当前状态
- 测试基线：NNN passed（`cd backend && uv run --extra dev pytest tests/ --ignore=tests/test_doctor_script.py -q`）
- GitHub：https://github.com/bog5d/cangjie-fos（master 分支，最新 commit：XXXXXXX）

### 本轮做完了什么
[按功能分组，3-5条，每条一句话]

### 待处理（下一版从这里开始）
| Bug | 现象 | 入手文件 |
|-----|------|---------|
| #X | ... | `路径` |

### 不能推翻的架构约定
[从 CLAUDE.md 直接摘录关键约定，3-5条]

### 接手第一步
\`\`\`bash
git clone https://github.com/bog5d/cangjie-fos.git
cd cangjie-fos/backend
uv run --extra dev pytest tests/ --ignore=tests/test_doctor_script.py -q
# 期望：NNN passed，0 failed
\`\`\`

NNN 通过 = 环境正常，可以开始开发。详细架构见 CLAUDE.md（根目录）。
---
```

---

### 第4步：提交 CLAUDE.md 更新

```bash
git add CLAUDE.md
git commit -m "docs: vX.Y.Z 交接文档更新 — 改动文件清单 + 待处理问题"
git push origin master
```

---

### 第5步：报告完成

向用户输出：
```
✅ 交接包已生成

已更新：CLAUDE.md（改动文件清单 + 接手速览）
已推送：GitHub master（commit: XXXXXXX）

下方是「直接粘给下一个 AI」的交接 Prompt，复制全段即可：
[输出第3步生成的 Prompt]
```

---

## 输出质量约定

- 交接 Prompt 必须**自包含**：新 AI 粘贴后不需要再问你任何问题就能开始
- 「待处理问题」必须写**入手文件路径**，不能写「需要调查」
- 「本轮做完了什么」用动词开头，说结果不说过程（「新增了 X 功能」而不是「我修改了 Y 文件来实现 Z」）
- 「不能推翻的约定」只写会让新 AI 犯错的那几条，不要复制全部 CLAUDE.md

---

## 适用场景

- 一个功能/Bug 批次完成，准备发版或交给另一个 AI 继续
- 上下文快满了，需要开新会话继续
- 你（王波）要把任务交给另一台设备或另一个工具
