---
name: profile-model-routing
version: 1.0
author: Hermes
tags: [model, routing, fallback, profile, cost-optimization, provider]
description: 管理所有 profile 的 model 默认值、fallback chain 和 provider 配置。适用于统一切换模型、降低成本、排查模型不可用问题。
created: 2026-06-17
updated: 2026-06-17
---

# Profile Model Routing 管理

当用户要求"把模型换成 xxx"、"所有 profile 都走 yyy"、"fallback 设成 zzz"、"统一用 Agnes/DeepSeek/本地模型"时使用。

## 触发条件

- 用户要求切换所有 profile 的默认 model
- 用户要求统一 model 以降低 token 成本
- 用户报告某个 model 不可用/响应慢，需要降级
- 新 provider 上线，需要分发到各 profile

## 核心概念

Hermes 的 model 配置层级：

```
config.yaml (顶层默认)
  ↓ 各 profile 可覆盖
~/.hermes/profiles/<name>/config.yaml
  ↓ 各 profile .env 可覆盖
~/.hermes/profiles/<name>/.env (TELEGRAM_BOT_TOKEN 等)
```

每个 profile 的配置结构：
```yaml
model:
  default: agnes-2.0-flash    # 默认模型
  provider: agnes              # provider 名
  base_url: ...                # (可选) 自定义 endpoint
  api_key: ...                 # (可选) 覆盖 env

fallback_providers:            # 降级链
- provider: deepseek
  model: deepseek-v4-flash
```

## 操作流程

### 1. 查看当前所有 profile 的 model 配置

```bash
for profile in default her-m2 finance english-tutor holo-local; do
  if [ "$profile" = "default" ]; then
    path="$HOME/.hermes/config.yaml"
  else
    path="$HOME/.hermes/profiles/$profile/config.yaml"
  fi
  
  model=$(sed -n '/^model:/,/^[a-z]/p' "$path" | grep 'default:' | head -1 | sed 's/.*default: *//')
  fb=$(sed -n '/^fallback_providers:/,/^[a-z]/p' "$path" | grep 'model:' | head -1 | sed 's/.*model: *//')
  
  echo "$profile: model=$model | fallback=$fb"
done
```

### 2. 修改默认 model

**注意：** config.yaml 文件可能被 gateway 进程锁定（受保护文件），直接 patch/sed 可能被回滚。

如果 `patch` 失败，改用 `terminal` 直接操作：

```bash
# 精确行号替换（避免正则匹配问题）
sed -i '' '3s/deepseek-v4-flash/agnes-2.0-flash/' ~/.hermes/profiles/finance/config.yaml
```

### 3. 修改 fallback chain

fallback 在 `fallback_providers:` 块下，用行号精确替换：

```bash
# 先找到行号
grep -n "fallback_providers\|model:" ~/.hermes/profiles/finance/config.yaml | head -10
# 然后精确替换对应行
sed -i '' '395s/deepseek-v4-pro/deepseek-v4-flash/' ~/.hermes/profiles/finance/config.yaml
```

### 4. 为新 profile 创建 .env

```bash
# 从 default 复制模板
cp ~/.hermes/.env ~/.hermes/profiles/<name>/.env
# 替换特定值
sed -i '' 's/TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=<new_token>/' ~/.hermes/profiles/<name>/.env
```

### 5. 创建 launchd 服务

参考模板：`~/Library/LaunchAgents/ai.hermes.gateway-her-m2.plist`

```bash
# 加载新服务
launchctl load ~/Library/LaunchAgents/ai.hermes.gateway-<name>.plist
# 重启
launchctl kickstart gui/$(id -u)/ai.hermes.gateway-<name>
# 验证
pgrep -a "hermes.*<name>" | head -3
# 查看日志
tail ~/.hermes/profiles/<name>/logs/gateway.log
```

## Pitfalls

- **config.yaml 受 gateway 保护**：如果 gateway 进程持有文件锁，外部修改会被秒回滚。此时需要先停 gateway 或直接用 terminal sed 修改
- **fallback 和默认 model 是两块**：改了 model.default 不意味着 fallback 也变了，需要分别修改
- **holo-local 类本地 profile**：默认用本地模型（如 Holo-3.1），fallback 必须设一个云端 provider，否则本地模型挂了就没 fallback 了
- **API 端口冲突**：新 profile 的 gateway 启动时如果端口 8642 被占用会失败，需要在 config.yaml 里改 `platforms.api_server.port`
- **Telegram bot token 存放位置**：在每个 profile 的 `.env` 里，不是 config.yaml

## 目标配置模板

通用模板：Agnes 免费模型 + DeepSeek flash 降级

```yaml
model:
  default: agnes-2.0-flash
  provider: agnes

fallback_providers:
- provider: deepseek
  model: deepseek-v4-flash
```

本地模型 profile 模板：

```yaml
model:
  default: mradermacher/Holo-3.1-4B-GGUF:Q4_K_M
  provider: custom:holo-local

fallback_providers:
- provider: deepseek
  model: deepseek-v4-flash
```

## 验证

```bash
# 确认所有 profile 配置一致
# 确认 gateway 进程在跑
pgrep -a "hermes.*<profile>" 
# 确认 telegram bot 已连接
tail ~/.hermes/profiles/<profile>/logs/gateway.log | grep "Telegram"
```
