---
name: clash-verge-management
title: Clash Verge Profile & Node Management
description: "Proxy fails for AI? Diagnose, merge, restart core."
trigger: "User asks why a site (ChatGPT/OpenAI/Claude) won't load; general proxy troubleshooting; Clash profile switching"
---

# Clash Verge Profile & Node Management

Diagnose and fix proxy connectivity issues on macOS Clash Verge (mihomo kernel).

## 🎯 用户偏好（铁律）

当用户说「你能不能帮我操作好」、「你现在就能给我弄好不嘛」、「我不在电脑旁」等要求直接行动的指令时：
**禁止**：解释「为什么不行」、分析问题根因、列出不可行的方案
**必须做**：直接操作解决问题（通过 computer_use 或 API）。如果确实无法在后台完成，操作到哪一步就汇报到哪一步——而不是「这个问题是XXX，建议你YYY」。

核心原则：**Action over analysis。修复未遂 > 完美诊断**。

## Diagnostic Flow

### 1. Isolate the problem layer

```bash
# Test local network
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 https://www.baidu.com

# Test proxy (will go through Clash at mixed-port)
curl -s -o /dev/null -w "%{http_code} | %{time_total}s" -x http://127.0.0.1:7897 --connect-timeout 10 https://chatgpt.com

# Test direct (no proxy) to see if GFW blocks it
curl -s -o /dev/null -w "%{http_code} | %{time_total}s" --noproxy "*" --connect-timeout 10 https://chatgpt.com
```

### 2. Interpret HTTP codes

| Code | Meaning |
|------|---------|
| 200 | Site works |
| 000 / timeout | GFW block or DNS failure |
| 403 (cf-mitigated) | **Cloudflare WAF blocking proxy IP** — the root cause 90% of OpenAI/ChatGPT failures |
| 403 (other) | Site-specific block (login/auth) |

### 3. Check Cloudflare WAF

```bash
curl -sI -x http://127.0.0.1:7897 --connect-timeout 10 https://chatgpt.com | grep -i cf
```

Look for: `cf-mitigated: challenge` → IP-level block.

## Profile & Node Discovery

Master config: `~/Library/Application\ Support/io.github.clash-verge-rev.clash-verge-rev/profiles.yaml`

Profile files are in the `profiles/` subdirectory. L*.yaml files contain the full config. p-prefixed files contain proxy overrides.

**Key technique**: Same UUID + different server IP = same subscription, different egress. Scan all profiles for backup IPs.

## Creating & Importing a Merged Config

1. **Create profile file** → `profiles/<name>.yaml` with all nodes + url-test groups + AI rules
2. **Create companion files** (m_<uid>.yaml, s_<uid>.js, r_<uid>.yaml, p_<uid>.yaml, g_<uid>.yaml)
3. **Register in profiles.yaml** via Python yaml.safe_load/dump
4. **Apply to runtime**: `cp profiles/<new>.yaml clash-verge.yaml && cp profiles/<new>.yaml clash-verge-check.yaml`
5. **Restart kernel**: `curl -s -X POST --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/restart`
6. **Verify**: `curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/proxies`

## cua-driver 故障恢复

当 computer_use 返回 0x0 capture / list_apps 空 / list_windows 空时，cua-driver MCP bridge 可能断连（常见于 cua-driver serve 运行 7+ 天）。

**重启流程**：
1. Kill 旧 serve 进程（pid 可通过 `ps aux | grep "cua-driver serve"` 找到）
2. 用 `terminal(background=true)` 启动 `/Applications/CuaDriver.app/Contents/MacOS/cua-driver serve`
3. 用 `terminal(background=true)` 启动 `/Users/mac/.local/bin/cua-driver mcp --no-overlay`
4. 等待 2-3 秒再试 capture

注意：不要用 foreground+&（被拦截），必须用 background 模式。

## 节点全被封时的处理

如果所有代理节点都返回 403 (cf-mitigated: challenge)：

1. **尝试浏览器**：Safari/Chrome 能执行 Cloudflare JS 验证码，通过 `open -a Safari 'https://chatgpt.com'` 启动后浏览器可以正常访问
2. **更新订阅**：通过 Clash API 或 GUI 更新订阅，新 IP 可能未被封
3. **换订阅商**：同订阅商的不同节点通常共享 IP 段声誉，建议整家换

## Pitfalls

- Same provider = same IP reputation. All IPs may be blocked together.
- `clash-verge.yaml` + `clash-verge-check.yaml` **both** need updating.
- No auto-detect on profiles.yaml change → must restart core.
- Use `url-test` (not `fallback`) for AI groups.
- Browser can pass Cloudflare JS challenges that curl can't.
