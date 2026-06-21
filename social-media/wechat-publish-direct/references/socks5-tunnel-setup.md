# SOCKS5 隧道 — 固定出口 IP 方案

## 问题

本机宽带 IP 动态变化（C-G NAT），微信公众平台 IP 白名单无法跟上。需要固定出口 IP。

## 方案

SSH SOCKS5 隧道 → 阿里云 ECS `47.85.62.133`（固定公网 IP）→ 微信 API。

## SSH 密钥

路径：`/Users/mac/.ssh/id_ed25519_alicloud`

## 启动隧道

```bash
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -i /Users/mac/.ssh/id_ed25519_alicloud \
  -D 1080 -N -f root@47.85.62.133
```

- `-D 1080`：本机 SOCKS5 监听端口
- `-N`：不执行远程命令
- `-f`：后台运行
- `ServerAliveInterval=30`：防止闲置断开

## 验证隧道

```bash
# 检查进程
pgrep -f "ssh.*1080.*47.85"

# 测试微信 API 通过隧道
curl -s --socks5 127.0.0.1:1080 --connect-timeout 8 \
  'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=APPID&secret=SECRET'
```

## 使用 publish_article.py

```bash
python3 scripts/publish_article.py \
  --article /tmp/article.md \
  --socks5 127.0.0.1:1080
```

## 技术细节

### 路由白名单

`publish_article.py` 只在连接 `api.weixin.qq.com` 时走 SOCKS5，其他域名（`api.deepseek.com`、`picsum.photos`）直连。

实现：`_build_request()` 检查 `host in SOCKS5_HOSTS`。

### 本地 DNS

因为阿里云服务器 DNS 解析失败（`/etc/resolv.conf` 无效），SOCKS5 连接使用**本地 DNS**：
- 客户端先解析 `api.weixin.qq.com` → IP
- 通过 SOCKS5 CONNECT 请求连接 IP（ATYPE=0x01 IPv4）

PySocks 不支持此模式（它发 hostname，由 proxy 端解析 DNS），故脚本内置最小 SOCKS5 连接器。

### 最小 SOCKS5 连接器

```python
def _socks5_connect(target_host, target_port, timeout=15):
    import struct
    ip = socket.getaddrinfo(target_host, target_port)[0][4][0]  # 本地解析
    proxy_host, proxy_port = SOCKS5_PROXY
    sock = socket.create_connection((proxy_host, proxy_port), timeout=timeout)
    # 握手: 0x05 0x01 0x00 (version, 1 method, no auth)
    sock.sendall(b'\x05\x01\x00')
    resp = sock.recv(2)
    if resp != b'\x05\x00':
        raise OSError(f"Handshake failed: {resp.hex()}")
    # CONNECT: 0x05 0x01 0x00 0x01 + IP + PORT
    req = b'\x05\x01\x00\x01' + socket.inet_aton(ip) + struct.pack('!H', target_port)
    sock.sendall(req)
    resp = sock.recv(10)
    if resp[1] != 0x00:
        raise OSError(f"Connect failed: code={resp[1]}")
    return sock
```

零外部依赖，纯 `struct + socket`。PySocks 不可靠（行为不一致），已弃用。

## 故障排查

### 隧道断开

```bash
# 杀掉旧进程，重新启动
pkill -f "ssh.*1080.*47.85"
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -i /Users/mac/.ssh/id_ed25519_alicloud \
  -D 1080 -N -f root@47.85.62.133
```

### 微信 API 超时

1. 确认隧道进程存在：`pgrep -f "ssh.*1080.*47.85"`
2. 确认阿里云可达：`ssh -i ~/.ssh/id_ed25519_alicloud root@47.85.62.133 echo OK`
3. 确认微信 IP 可达：`curl -s --socks5 127.0.0.1:1080 https://api.weixin.qq.com`
