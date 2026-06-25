# Tunnel Troubleshooting — 实时档案馆隧道排查指南

2026-06-25 真实事故后整理。当 @Engcjd_bot 发的「实时档案馆」链接打不开时，按此流程排查。

## 快速诊断（10秒）

```bash
# 1. 端口 8765 有 HTTP 服务器吗？
lsof -ti :8765 || echo "NO HTTP on 8765"

# 2. SSH 隧道存活？
ps aux | grep 'localhost.run' | grep -v grep

# 3. tunnel_url.txt 内容
cat /Users/mac/.hermes/profiles/english-tutor/state/tunnel_url.txt 2>/dev/null

# 4. 自测 URL 可用性
URL=$(cat ~/.hermes/profiles/english-tutor/state/tunnel_url.txt 2>/dev/null)
curl -s -o /dev/null -w "HTTP %{http_code}\n" "$URL/chronicle_index.html" --connect-timeout 5
```

## 一键修复

```bash
python3 /Users/mac/.hermes/profiles/english-tutor/state/start_tunnel.py
```

这个脚本：
1. 启动 HTTP server on 8765（serving state/ 目录）
2. 建立 SSH tunnel via localhost.run
3. 写入新 tunnel_url.txt
4. 自测 HTTP 200 确认

## 三种常见故障模式

### 模式 A: 端口冲突（最常见）
**现象**：孤儿 HTTP server 在 9876 运行，8765 空闲。tunnel_url.txt 有值但指向死隧道。

**诊断**：
```bash
lsof -ti :8765  # 空 → 服务没启动
lsof -ti :9876  # 有 PID → 孤儿服务
```

**修复**：kill 9876 → `python3 -m http.server 8765` 在 state/ 下启动

### 模式 B: SSH 隧道过期
**现象**：8765 有 HTTP 服务，但 localhost.run 进程不存在。

**诊断**：
```bash
ps aux | grep 'localhost.run' | grep -v grep  # 空 → 隧道死了
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8765/chronicle_index.html"  # 200 → 本地OK
```

**修复**：重新建立 SSH 隧道

### 模式 C: URL 完全过期（最隐蔽）
**现象**：HTTP 服务和隧道都活着，但 tunnel_url.txt 存的 URL 是几天的老 URL。

**诊断**：
```bash
ps aux | grep 'localhost.run' | grep -v grep  # 有进程
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8765/chronicle_index.html"  # 200
# 但公网 URL 自测失败
curl -s -o /dev/null -w "%{http_code}" "$(cat tunnel_url.txt)/chronicle_index.html"  # 503
```

**修复**：运行 start_tunnel.py 获取新 URL

## session_pipeline.py 的死 URL 陷阱

`session_pipeline.py` 在 line ~905 从 `tunnel_url.txt` 直接读取 URL，不做任何可用性检查。
即使隧道已死多日，只要 txt 文件存在，输出 JSON 就会包含 `tunnel_url` 字段。

**LLM 防御**：不要信任 pipeline 的 `tunnel_url` 字段。发 URL 前必须自测 HTTP 200。
