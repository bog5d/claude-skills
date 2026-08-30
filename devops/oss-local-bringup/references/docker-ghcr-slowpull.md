# Docker 部署实录：ghcr.io 慢拉与后台等待模式（freellmapi，2026-08-30）

场景：`/Users/mac/oss-lab/freellmapi`（tashfeenahmed/freellmapi，34 免费供应商聚合路由）。

## 步骤实录

1. **生成 .env**（仓库只带 `.env.example`，compose 引用 `env_file: .env`）：
```bash
cd /Users/mac/oss-lab/freellmapi
printf "ENCRYPTION_KEY=%s\nPORT=3001\n" "$(openssl rand -hex 32)" > .env
chmod 600 .env
```
2. **起容器**：`docker compose up -d` 挂 background=true + notify_on_complete=true。
3. **等待期信号判读**：
   - `docker compose ps` 无容器 + `docker images` 为 0 = 镜像还在拉，正常。
   - Docker Desktop 走系统代理（`docker info` 可见 `HTTP Proxy: http.docker.internal:3128`），ghcr.io 大镜像过代理 15-20 分钟属常态，不要提前判死。
   - 拉完 compose 自动起容器，healthcheck 打 `http://127.0.0.1:3001/api/ping`。

## 关键认知

- **前台跑 compose 会被工具闸拦**（判定为长驻进程）。正确拆分：写 .env 等短命令前台，`up -d` 后台。
- **前台 `docker pull` 摸进度是陷阱**：它本身也要几分钟+，会白吃一次 timeout 且和后台 compose 抢同一镜像层。
- 该项目 Web UI 在 3001 端口（Keys 页录供应商 key、Fallback Chain 排序、拿统一 API key），绑定 127.0.0.1 单用户设计，不暴露公网。
- 安全红线（对波总）：免费池请求会流向第三方供应商，只跑低风险负载，禁接 FOS 代码/尽调数据。

## 状态（本会话结束时）

- .env 已生成 ✅；镜像拉取中（后台 proc 挂 notify，拉完自动起容器）；容器健康检查与 Hermes fallback 链接入未完成，留给下一个会话接手。
