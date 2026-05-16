---
name: cronjob-troubleshooting
version: 1.0
author: Hermes
tags: [cron, debugging, troubleshooting, scheduled-tasks]
description: 排查Hermes Agent定时任务执行失败的调试流程，包括检查任务状态、查看执行日志、分析错误原因
created: 2026-04-18
updated: 2026-04-18
---

# Cronjob故障排查

当用户报告定时任务没有按预期执行时，使用此技能进行系统化排查。

## 触发条件

- 用户报告“定时任务没有执行”或“提醒没有收到”
- 系统时间已过预定执行时间
- 需要验证cronjob是否正常运行

## 排查步骤

### 1. 验证系统时间
首先检查当前系统时间是否已过预定执行时间：
```bash
date
```

### 2. 检查活跃任务列表
查看当前配置的cronjob：
```bash
cronjob action=list
```

如果列表为空，说明任务可能已被删除或从未创建成功。

### 3. 检查cron目录结构
查看cron目录下的文件和子目录：
```bash
ls -la ~/.hermes/cron/
ls -la ~/.hermes/cron/output/
```

### 4. 查找最近的执行记录
检查output目录中最新的子目录（按时间排序）：
```bash
ls -lt ~/.hermes/cron/output/ | head -5
```

### 5. 读取执行日志
进入最新的执行目录并查看日志文件：
```bash
read_file path=~/.hermes/cron/output/<job_id>/<timestamp_file>.md
```

或使用终端命令：
```bash
ls ~/.hermes/cron/output/
# 找到最新的job_id目录
ls ~/.hermes/cron/output/<job_id>/
cat ~/.hermes/cron/output/<job_id>/<timestamp_file>.md
```

### 6. 分析错误信息
常见错误模式：

| 错误类型 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `HTTP 502: Error code: 502` | 网关错误，API服务暂时不可用 | 重试发送，检查网络连接 |
| `API call failed after 3 retries` | 网络问题或认证失败 | 验证API密钥和连接 |
| `Job not found` | 任务已被删除或配置丢失 | 重新创建cronjob |
| `Schedule mismatch` | 时间格式错误或系统时区不匹配 | 检查schedule格式和系统时区 |
| `Delivery target unreachable` | 目标平台连接失败 | 检查send_message目标配置 |
| `任务重复执行（提醒了两次）` | `ONESHOT_GRACE_SECONDS=120`导致的oneshot任务恢复Bug | 见下方"重复执行排查"章节 |

### 7. 重复执行排查（一次性任务提醒了多次）

当用户报告"提醒了一次，过一会儿又提醒了一次"时：

**根因：`cron/jobs.py` 中的 `_recoverable_oneshot_run_at()` 的 grace 窗口太大**

```python
# ONESHOT_GRACE_SECONDS = 120  ← 120秒窗口
# 一次性任务完成后，如果gateway在120秒内重启或ticker抖动，
# _recoverable_oneshot_run_at() 会认为"任务还没执行过"，
# 再次恢复并执行，导致重复提醒
```

**排查确认步骤：**
1. 检查 `~/.hermes/cron/output/<job_id>/` 下是否有多个时间戳的输出文件（证明执行了多次）
2. 检查 `~/.hermes/cron/jobs.json` 中该任务是否已被删除（oneshot执行后正常会删除）
3. 确认 gateway 是否在该时间段内重启过

**修复方案：**
- 将 `ONESHOT_GRACE_SECONDS` 从 120 缩小到 10
- 或在 `mark_job_run()` 中给已执行的 oneshot 任务在 jobs.json 中添加 `"completed": true` 标记，`_recoverable_oneshot_run_at()` 检查该标记跳过恢复
- 两个修复都做最保险

**代码位置：**
- `cron/jobs.py` — `_recoverable_oneshot_run_at()` 函数（grace判定）
- `cron/jobs.py` — `mark_job_run()` 函数（任务完成标记）

### 8. 检查jobs.json配置文件
查看cronjob配置文件：
```bash
read_file path=~/.hermes/cron/jobs.json
```

确认任务是否在配置中，以及配置是否正确。

### 8. 重新创建或重试
根据错误原因：
- 对于临时性错误（如HTTP 502），建议用户重试发送
- 对于配置问题，重新创建cronjob
- 对于平台连接问题，测试平台连接状态

## 验证步骤

1. **确认任务已成功执行**：检查output目录中是否有新的执行记录
2. **验证错误已解决**：重新创建后，等待下一次执行时间验证
3. **测试平台连接**：使用`send_message action=list`检查平台连接状态

## 注意事项

- cronjob使用本地系统时间，确保时区正确
- 一次性任务（`schedule: once in Xm`）执行后会自动删除
- 重复性任务会持续存在直到手动删除
- HTTP 502等网关错误通常是暂时性的，可能需要重试

## 示例

用户报告：“你提醒我11:58左右，但现在已经12点了，也没有给我任何提醒”

排查流程：
1. `date` → 确认当前时间已过12:00
2. `cronjob action=list` → 可能为空（一次性任务已执行并删除）
3. `ls -la ~/.hermes/cron/output/` → 查找最近的执行记录
4. 找到最新的job_id目录，读取日志文件
5. 发现“API call failed after 3 retries: HTTP 502”
6. 结论：任务已执行但API调用失败，需要重试发送提醒