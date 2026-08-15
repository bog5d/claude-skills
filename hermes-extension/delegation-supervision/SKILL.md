---
name: delegation-supervision
description: "后台子代理/Cursor长任务运行中，波总问报进度时：tail 实时日志如实播报+提前发现卡死。"
---

# 后台任务监督与进度汇报

## 触发条件
- `delegate_task` 已派发后台子代理（尤其 Cursor CLI 长任务：下载/OCR/转写/批量处理）
- 波总在任务运行中问"报进度"/"进度如何"/"好了没"
- 需要判断后台子代理是否卡死（静默空转、反复重试）

## 核心机制：live_transcripts

`delegate_task` 派发后返回 `live_transcripts` 路径：`~/.hermes/cache/delegation/live/<deleg_id>/task-0.log`
- append-only 流式日志，实时写入子代理的 assistant 文本、tool 调用、tool 结果
- 主代理可随时 `tail` 它，不需要等子代理结束

## 报进度规范（波总明确偏好）

```bash
tail -50 ~/.hermes/cache/delegation/live/<deleg_id>/task-0.log
```

从日志提取**真实状态**，按结构汇报：
- ✅ 已完成步骤（下载/解压/OCR/写文件…实际出现在日志里的）
- 🔴 当前正在做什么
- 下一步是什么

**绝对禁止**：只回一句"还在跑/正在处理"——波总要的是从日志里读出的实况，不是状态占位。参考格式：
```
🔴 [Cursor 执行中] 进度实时播报：
✅ 已完成：下载解压成功（10个PDF）→ OCR 全部完成
🔴 当前：正在合并成 Markdown
```

## 卡死检测（提前干预，不等用户问）

tail 日志时发现以下信号 = 子代理卡死，应主动干预（kill + 重新派发，或派发修正指令）：
- 同一个 tool 调用重试 3 次以上且都失败
- 日志尾部长时间（数分钟）无新增内容
- 反复报同一个错误（如 OCR 路径 bug、下载 0 字节）
- 子代理声称"完成"但无对应文件落盘（侧效应验证，见 cursor-default-executor）

## 验证侧效应（完成汇报前必做）

子代理自报完成 ≠ 完成。汇报前必须亲自验证：
- 文件存在 + 大小合理：`ls -la <path>` / `wc -l <path>`
- 内容覆盖：`grep -n "^#" <md>` 检查章节齐全
- 结构抽查：打开关键段落确认不是空壳
验证通过才向用户报"完成"。

## 相关技能
- `cursor-default-executor` — Cursor 执行铁律与调度规范（受保护，勿改）
- `hermes-memory-curation` — 记忆容量管理
