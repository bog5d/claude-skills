# Profile 端口分配地图

多 profile 共享同一台机器时，API server 端口必须互斥分配。

## 当前分配

| Profile | Service | Port | 用途 |
|---------|---------|------|------|
| default | `ai.hermes.gateway` | 8642 | API server (main) |
| english-tutor | `ai.hermes.gateway-english-tutor` | 8644 | API server + HTTP tunnel (8765) |
| her-m2 | `ai.hermes.gateway-her-m2` | — | 无 api_server |
| finance | `ai.hermes.gateway-finance` | 8646 | API server |
| headroom | `com.hermes.headroom-proxy` | 8787 | Anthropic API proxy |

## 新增 profile 时

```bash
# 1. 扫描已占用端口
lsof -ti:8642  # default
lsof -ti:8644  # english-tutor
lsof -ti:8646  # finance

# 2. 分配下一个可用偶数端口 (8648, 8650, ...)
```

## 修改端口（两个 key 必须同步）

```bash
/Users/mac/.hermes/hermes-agent/venv/bin/python3 -c "
import yaml
path = '<profile>/config.yaml'
with open(path) as f: cfg = yaml.safe_load(f)
cfg['api_gateway']['port'] = <NEW_PORT>
cfg['platforms']['api_server'] = {'enabled': False, 'extra': {'host': '127.0.0.1', 'port': <NEW_PORT>}}
with open(path, 'w') as f: yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
"
launchctl kickstart -k gui/501/<service>
```

## 陷阱

- `enabled: false` **不阻止初始化**，gateway 仍尝试绑定端口
- 删除 `platforms.api_server` 段也无用——gateway 回退到默认 8642
- **必须显式设置非冲突端口**，且 `api_gateway.port` 和 `platforms.api_server.extra.port` 同步
