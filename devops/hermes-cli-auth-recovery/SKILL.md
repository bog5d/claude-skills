---
name: hermes-cli-auth-recovery
description: Use when CLI 工具（cursor-agent等）报认证失败。降级备用引擎前先修认证。
---

# CLI 工具认证恢复（cursor-agent 实战手册，2026-09-07 全流程验证）

## 触发条件
- 执行引擎报 `Authentication required` / `Please run 'agent login' first`
- delegate_task 或 ACP 调用 Cursor/其他 CLI 子代理认证失败
- **降级到备用引擎（Hermes 原生）之前，先走本流程修认证**——不要直接降级

## 症状识别（先分清是哪类问题）

| 现象 | 真实含义 | 动作 |
|------|----------|------|
| `cursor-agent status` → `✓ Login successful! (unable to fetch user details)` | **不可信**。常伴随实际未认证 | 用 `-p` 实测 |
| `cursor-agent -p` → `Authentication required` | 确实未认证 | 走 login 流程 |
| `cursor-agent -p` → `Pass --trust, --yolo, or -f` | **不是认证问题**，是目录信任确认 | 加 `--trust` 重试 |
| login exit=1 + 日志尾 `Login failed or timed out` | 授权链接没被完整走完 | 重发新链接 |

## Login 恢复流程（已验证）

```bash
# 1. 必须 background 跑——前台实测 60s/30s 两次挂死超时
cd /tmp && NO_OPEN_BROWSER=1 cursor-agent login > /tmp/cursor_login.log 2>&1
# terminal(background=true, notify_on_complete=true)

# 2. 等约 4 秒提取授权链接
grep -o 'https://cursor.com/loginDeepControl[^ ]*' /tmp/cursor_login.log

# 3. 链接发给用户完成登录；可选 `open <链接>` 在 Mac 上同时打开

# 4. 用户完成后验证
tail -3 /tmp/cursor_login.log                     # 期望: ✓ Logged in as <email>
cursor-agent -p --trust "请只回复两个字:在线"        # 期望: 在线
```

## 关键事实（实测结论，勿重复踩坑）

- **手机点授权链接可行**（2026-09-07 实测：链接发手机、用户手机完成登录 → 回调成功 exit=0）。失败的真实原因是登录页没走完整（中途关页面），不是"手机回调不到本机"。**未验证前不要向用户断言失败原因。**
- **login 前台跑必挂**，必须 background。
- **非交互执行几乎总需要 `--trust`**（非白名单目录下），报错文案极易误读成认证问题。
- **IDE 登录 ≠ CLI 认证**：Cursor IDE 的 state.vscdb 有 accessToken 不代表 cursor-agent 已认证，两套独立存储。
- 网络排查：`curl -x http://127.0.0.1:7897 https://api2.cursor.sh`（波总本机 Clash 代理）；历史上有代理节点被 Cursor CDN 封导致 TLS 断连，换节点解决。
- Plan B：Cursor Dashboard → API Keys 生成 key → `cursor-agent login --api-key <key>` 或 `CURSOR_API_KEY` 环境变量。
- 安全红线：不打印 token/challenge 值；loginDeepControl 链接本身可以发给用户。

## 通用化（其他 CLI 同理）
1. 先分清三类错误：认证缺失 / 目录信任 / 网络不通——报错文案会骗人，用最小实测命令区分
2. 认证恢复优先后台跑 + 把授权链接交给用户，别前台阻塞
3. 修好后再决定是否需要降级
