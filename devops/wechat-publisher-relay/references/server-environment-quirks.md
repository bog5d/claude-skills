# 47.85.62.133 环境实测速查表 (2026-06-10)

## 系统规格

| 项 | 值 |
|---|-----|
| OS | Alibaba Cloud Linux 3 (OpenAnolis), kernel 5.10 |
| CPU | 2 核 |
| RAM | 1.8GB (可用 ~400-700MB 浮动) |
| Swap | 8GB |
| 磁盘 | 40GB (已用 26G, 可用 13G) |

## Python 环境

```
系统默认: /usr/bin/python3 → Python 3.6.8 (太老，不要用)
Miniconda: /root/miniconda3/bin/python → Python 3.13.11 ✅
Conda env: /root/miniconda3/envs/aider_env/ → Python 3.10
```

**铁律**：任何需要 Python 3.8+ 的操作，必须先 `export PATH="/root/miniconda3/bin:$PATH"`。

## Node.js 环境

```
Node: 已安装（通过 wx-publisher PM2 管理）
npm: 可用，设置国内源: npm config set registry https://registry.npmmirror.com
```

## Docker 环境

| 项 | 值 |
|---|-----|
| 版本 | Docker 26.1.3 |
| 运行容器 | rustdesk-hbbs, rustdesk-hbbr |
| **关键缺陷** | **容器内 DNS 不通外网** |

### Docker DNS 问题

宿主机 DNS 正常（100.100.2.136/138），但 Docker 容器内无法解析 deb.debian.org / mirrors.aliyun.com / registry.npmjs.org 等域名。`apt-get update` 和 `npm install` 在容器内均超时。

**已尝试的修复（均失败）**：
- 写入 `/etc/docker/daemon.json` 的 DNS 配置 → 重启 Docker → 容器 DNS 仍不通
- 使用阿里云 Debian/NPM 镜像源 → 容器仍无法解析镜像域名

**有效对策**：**绕过 Docker，直接在宿主机上安装运行。** 宿主机 DNS 正常，npm/pip 均可连通。

**预拉取镜像可能成功**（`docker pull` 走 registry mirror），但构建阶段的 apt/npm 必定失败。如需容器化部署，考虑：
1. 使用预构建镜像（本地 build 好 push 到 registry，服务器直接 pull）
2. 在 Dockerfile 中使用 `--network=host`（BuildKit 语法，需 DOCKER_BUILDKIT=1）
3. 先手动在宿主机安装所有依赖，再 COPY 进容器

## 端口占用

| 端口 | 进程 | 对外 |
|------|------|------|
| 22 | sshd | ✅ |
| 8787 | wx-publisher (PM2) | ✅ |
| 7000 | frps | ✅ |
| 6000 | frps | ✅ |
| 21115-21119 | Docker rustdesk | ✅ |
| 18789/18792 | moltbot-gateway | ❌ localhost only |
| 8000 | 空闲（预留给仓颉 FOS） | ❌ |

## 🔑 SSH 连接

```
密钥: /Users/mac/.ssh/id_ed25519_alicloud (Mac Mini 本地)
或密码: (见 mem0)
IP: 47.85.62.133
用户: root

⚠️ Hermes $HOME 重写陷阱: ~/.ssh/ 会解析到 profile 路径
   必须用绝对路径: ssh -i /Users/mac/.ssh/id_ed25519_alicloud root@47.85.62.133
```

## 已部署服务

| 服务 | 管理方式 | 用户 | 启动方式 |
|------|---------|------|---------|
| wx-publisher | PM2 | root | `pm2 restart wx-publisher` |
| moltbot-gateway | systemd | admin | `systemctl restart moltbot` |
| rustdesk-hbbs/hbbr | Docker | root | `docker restart rustdesk-hbbs` |
| frps | 手动进程 | root | `kill frps && nohup frps ... &` |

## 阿里云安全产品

- AliYunDun (云盾) 运行中 — 不要停止
- cloudmonitor (云监控) 运行中
- 防火墙由 firewalld 管理，安全组在阿里云控制台

## SSH 爆破现状

持续遭受扫描（80.94.92.x，尝试 sol/ubuntu/binance 等用户名），但 `PasswordAuthentication no` + 仅 2 把 authorized_keys 有效挡住了所有攻击。没有被攻破的痕迹。
