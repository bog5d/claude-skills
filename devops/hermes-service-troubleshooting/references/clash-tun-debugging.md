# Clash Verge Rev (Mihomo) TUN/DNS 调试

## 环境

- Clash Verge Rev 使用 mihomo 内核
- TUN 模式：`enhanced-mode: fake-ip`，DNS 劫持 `any:53`
- Fake IP 段：`198.18.0.1/30`
- 对外 API：Unix socket `/tmp/verge/verge-mihomo.sock`
- 系统代理：HTTP/SOCKS5 在 `127.0.0.1:7897`

## 关键 API 端点（通过 Unix socket）

```bash
# 看当前规则
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/rules

# 看配置（含 TUN/DNS 设置）
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/configs

# 看代理节点列表
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/proxies

# 看某个 selector 详情
curl -s --unix-socket /tmp/verge/verge-mihomo.sock \
  http://localhost/proxies/%E8%8A%82%E7%82%B9%E9%80%89%E6%8B%A9  # URL-encoded "节点选择"

# 切换 selector 节点
curl -s --unix-socket /tmp/verge/verge-mihomo.sock -X PUT \
  'http://localhost/proxies/%E8%8A%82%E7%82%B9%E9%80%89%E6%8B%A9' \
  -H 'Content-Type: application/json' -d '{"name":"DIRECT"}'
```

## 修改规则的正确方式

**Clash 的 `PUT /configs` API 不接受规则更新**（请求返回成功但规则不变）。必须：

1. **编辑配置文件** `~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml`
2. **用 yaml 库修改**（不能直接 sed，YAML 结构会被破坏）：

```python
import yaml
path = "/Users/mac/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml"
with open(path) as f:
    config = yaml.safe_load(f)

rules = config.get('rules', [])
# 在 GEOIP 规则前插入新规则
rules.insert(-2, 'DOMAIN,restapi.amap.com,DIRECT')
config['rules'] = rules

with open(path, 'w') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
```

3. **触发 Clash 重载**：

```bash
curl -s --unix-socket /tmp/verge/verge-mihomo.sock -X PUT http://localhost/configs \
  -H 'Content-Type: application/json' \
  -d '{"path":"/Users/mac/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml"}'
```

4. **验证规则生效**：

```bash
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/rules | python3 -c "
import sys,json; d=json.load(sys.stdin)
for r in d.get('rules',[]): print(f\"{r.get('type')}: {r.get('payload')} -> {r.get('proxy')}\")
"
```

## TUN 连接诊断流程

当某个域名在 TUN 模式下不可达时：

### 1. 区分 TCP vs SSL 问题

```bash
# TCP 是否可达
nc -zv -w 5 restapi.amap.com 443  # "succeeded!" = TCP OK

# SSL 握手是否正常
echo "Q" | openssl s_client -connect restapi.amap.com:443 -servername restapi.amap.com 2>&1 | head -10
# 如果 "no peer certificate available" → SSL 握手失败（服务器无响应）
# 如果正常显示证书链 → SSL OK，是上层协议问题
```

### 2. 隔离路由方式

```python
import httpx
# A. TUN 模式（trust_env=False）
with httpx.Client(trust_env=False, timeout=10) as c:
    r = c.get("https://restapi.amap.com/...")

# B. HTTP 代理（走 Clash 代理端口）
with httpx.Client(proxy="http://127.0.0.1:7897", timeout=10) as c:
    r = c.get("https://restapi.amap.com/...")

# C. SOCKS5h 代理（远程 DNS 解析）
with httpx.Client(proxy="socks5h://127.0.0.1:7897", timeout=10) as c:
    r = c.get("https://restapi.amap.com/...")
```

### 3. 对比已知可通的站点

```python
# 测试同类型中国服务是否可达
for url in ["https://www.baidu.com", "https://restapi.amap.com", "https://lbs.amap.com"]:
    try:
        with httpx.Client(trust_env=False, timeout=5) as c:
            r = c.get(url)
            print(f"✓ {url}: {r.status_code}")
    except Exception as e:
        print(f"✗ {url}: {type(e).__name__}")
```

## 已知问题：restapi.amap.com SSL 握手超时

**症状**：
- TCP 连接成功（`nc -zv restapi.amap.com 443 = succeeded`）
- SSL 握手超时 / `no peer certificate available`
- 无论 DIRECT、代理、TUN 模式均失败
- 同环境 `www.baidu.com` / `www.taobao.com` HTTPS 正常

**可能原因**：
- 运营商/中间节点对高德 API 443 端口做了干扰
- 高德 CDN 节点对某些地区 IP 不响应

**待验证**：浏览器能否直接访问 `https://restapi.amap.com/v3/weather/weatherInfo?city=110000&key=YOUR_KEY`
