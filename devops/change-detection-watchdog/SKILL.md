---
name: change-detection-watchdog
description: Use when 波总要盯某个东西、只在变化时才通知。静默 watchdog 模式。
---

# 静默变更监听（change-detection watchdog）

## 适用场景
"盯 X，只有发生变化时才叫我" 的任务：
- 考试/活动报名是否开放（如基金从业考试专场集体报名）
- 价格跌破阈值、商品上架、库存变化
- 服务/网站状态翻转（维护 ↔ 可打开）
- 公告/新闻/名单发布
- 任何"默认静默、变化才通知、日志自己留"的轮询

核心诉求：**平时零打扰、变化立刻叫、日志自己留**。

## 核心机制：no_agent + 空 stdout = 静默

`cronjob` 建任务时 `no_agent=True` + 自包含脚本：

- **非空 stdout = 原样投递通知**；**空 stdout = 静默**（无 LLM、零 token）。
- 通知逻辑全写进脚本，脚本自己决定这轮发不发。
- 脚本放 `~/.hermes/profiles/<profile>/scripts/`，cron 的 `script` 参数填相对文件名（`.py` 用 Python 跑，`.sh` 用 bash 跑）。

```python
cronjob(action='create', name='xxx-watch', no_agent=True,
        schedule='0 9-21/2 * * *', script='xxx_watch.py', deliver='origin')
```

## 状态机（关键）
- **状态文件**（JSON）记录上次结论：整数 `level`、关键标识（如公告 URL）、`last_notify` 时间戳。
- **首跑静默建基线**：无 state 文件时只落日志+状态，**绝不通知**（否则首跑必误报"有变化"）。
- **变化才通知**：结论升级/降级、或关键 URL 变化 → 立即发；持续无变化 → 每 N 天（如 3 天）一条极简状态；其余静默。
- 结论用整数 `level` 表达（如 0=维护中无公告 / 1=可打开未开 / 2=公告发 / 3=可操作），上升和下降都算"变化"（下降=又维护了，也值得报）。

## 降频 → 升级门控
平时 2 次/天，关键期每 2 小时：
- 调度用 `0 9-21/2 * * *`（每 2 小时都触发）；
- 脚本读 state 判断是否 critical：非 critical 时只在 09:00/15:00 完整探测，其它触发直接 `return`（零请求、静默）；critical 后每次触发都完整探测。

## 兜底
顶层 `try/except`：异常记日志、`exit(0)` 静默退出——避免 cron 对瞬态网络错误反复发"报错"。

## 时区
Hermes cron 用系统本地时区（config `timezone: ''` = 跟随系统）。中国机器 `date +%Z`=CST/Asia/Shanghai，`0 9 * * *` 即北京时间 9 点。写跨时区任务前先 `readlink /etc/localtime` 确认。

## 关键坑：JS SPA 页面探测（易误报）
探测"网站维护中 / 可打开"时，若目标站是 **JS 单页应用（SPA）**，`urllib`/`curl` 只拿到空壳（HTTP 200 + 空 title + 极小 HTML），"维护中/登录表单"文案由前端 JS 渲染 → **naive HTTP 探测误判"可打开"**，导致误报。

判定 SPA：HTTP 200 但 `len(html)` 极小（几百字节）、title 空、可见文本近乎 0。

对策（按优先级）：
1. 找**静态落地页**当权威信号（真静态 HTML，含按钮/维护文案，非 SPA）——最可靠、最轻量；
2. 无头 Chrome `--dump-dom` 渲染复核（见 references）。

## 用户判断与实测冲突时
用户说"现在是维护中"但脚本实测"可打开"——不要静默覆盖，也不要立刻 cry wolf。先用无头 Chrome 复核，再在**建立任务后的报告**里如实说明差异（可能维护已结束，或用户看到的是 SPA 内"暂无考试"状态），并按实测值设基线。

## 支持文件
- `references/silent-watchdog.md` — 可复用脚本骨架、无头 Chrome recipe、AMAC 报名监控实例（URL 现状 + SPA 判定实录）
