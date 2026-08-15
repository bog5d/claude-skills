---
name: hermes-memory-curation
description: "当 memory 工具报超限、占用>80%或规则未固化时，整理 MEMORY.md 容量。"
---

# Hermes 内置记忆容量管理

## 触发条件
- memory 工具 `add` 返回 "would exceed the limit" 错误
- 系统 prompt 头部 MEMORY/USER 占用显示 >80%
- 发现最新规则/偏好没有被及时固化（满仓的常见副作用）
- 用户问"memory 满了怎么办" / "是不是满了导致规则没生效"

## 核心事实
- MEMORY.md / USER.md 位于 `~/.hermes/memories/`，每轮注入系统 prompt，有严格字符上限
- 上限配置在 `config.yaml` 的 `memory.memory_char_limit`（默认 2200）/ `memory.user_char_limit`（默认 1375）
- memory 工具超限会报错并列出 `current_entries`，必须在同一轮内 `replace`/`remove` 腾位后再 `add`
- 官方最佳实践：**>80% 就该 consolidate，不要等满了**（官方文档明确："When memory is above 80% capacity, consolidate entries before adding new ones"）
- ⚠️ **满仓的隐性危害**：每次固化新规则都要先删旧条目 → agent 潜意识推迟固化 → 用户刚纠正的偏好/最新铁律落不了地（2026-08-15 实测：加"图片识别走Cursor"铁律时被拒一次，被迫先压缩旧条目）

## 整理流程（96% → 68% 实战验证）
1. 读当前条目（错误响应自带，或 `read_file ~/.hermes/memories/MEMORY.md`）
2. **优先删除已沉淀进技能的内容**——技能=按需加载、容量无限；memory=每轮付费注入、5000字符。同一信息存两处纯浪费：
   - 检索点：Clash技巧/微信预检/公众号作者/MEDIA规则/副官协议/机构问答口径等已进 skill 的条目
3. **合并同类项**：多条同主题条目并成一条信息密度高的（如两条 MV 规则 → 一条带优先级）
4. **历史教训精简**：保留"模型/权重/路径"等可复用事实，删掉一次性事件叙事（人名排序、完成日志）
5. **批量 operations 一次提交**（memory 工具原子批量，按最终结果检查上限，可先删后加腾位）
6. 目标：<80%（安全线），最好 <70%

## 扩容（必要时，非首选）
```bash
hermes config set memory.memory_char_limit 6000
hermes config set memory.user_char_limit 4000
```
⚠️ 调大 = 每轮 prompt token 增加（约 2.75 chars/token），适度即可。

## 自动维护（根治，2026-08-15 建立）
`scripts/memory_health_check.py` — 读 MEMORY.md/USER.md 实际占用 vs config 上限：
- <80% → 静默（watchdog 模式，不打扰）
- ≥80% → 🟡 提醒整理
- ≥90% → 🔴 必须立即整理

注册为 no_agent cron（脚本 stdout 即投递内容，空输出=安静）：
```
cronjob action=create no_agent=true script=memory_health_check.py schedule="0 9 * * 1"
```

## 组织原则（对齐波总 USER.md 定义）
- memory 只放：**48小时内活跃工作流 + 关键铁律 + 用户偏好**
- 已沉淀进技能 → 从 memory 删
- 任务进度/完成日志 → `session_search` 可查，不进 memory
- 外部深层记忆 → 走外部 provider（见 hermes-memory-provider-integration），与内置并行

## 验证
- 跑 `python3 ~/.hermes/scripts/memory_health_check.py` 看占用率
- 手工核对：去 frontmatter + `§` 分隔符后 `len()`（脚本同逻辑）
