# Tool Decision Matrix

| 场景 | 优先工具 | 备用工具 | 不推荐起手 |
|---|---|---|---|
| 读文件 | `read_file` | `search_files` | `terminal cat/head/tail` |
| 找文件 / 搜内容 | `search_files` | `read_file` | `terminal grep/find/ls` |
| 小范围改文件 | `patch` | `aider_edit` | `sed/awk` |
| 新建文件 / 覆盖整文件 | `write_file` | `patch` | shell heredoc |
| 复杂工程改动 | `aider_edit` | `patch` | 手工多次脆弱替换 |
| 简单网页检索 | `web_search` | `browser_navigate` | 直接 browser 全站乱点 |
| 动态页面 / 交互 | browser 工具链 | `web_search` + 提取 | 只靠网页搜索猜结果 |
| 多步分支逻辑 | `execute_code` | 顺序调工具 | 手工长链路反复调用 |
| 隔离式推理子任务 | `delegate_task` | `execute_code` | 主上下文硬扛全部中间过程 |
| 发送消息 | `send_message` | 无 | 用别的写入工具替代 |
| 定时 / 调度 | `cronjob` | terminal（仅必要时） | 手工模拟长期调度 |
| 只读系统状态检查 | `terminal` 只读命令 | `search_files` | 直接改系统状态 |

## 默认原则

- 能专用就不用通用
- 能只读就不先写
- 能小样本就不先全量
- 能验证就不靠猜
- 能 diff 就不盲改
