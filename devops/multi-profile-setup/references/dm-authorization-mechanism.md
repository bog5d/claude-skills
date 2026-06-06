# Hermes DM 授权机制 — 环境变量链

## 调用链

```
_should_process_message()   ← telegram.py: 群聊过滤 (allowed_chats 只在这起作用)
    ↓ DM 直接 return True   ← 不检查 allowed_chats！
    ↓
_is_user_authorized()        ← gateway/run.py:6949
```

## _is_user_authorized 检查顺序

1. HomeAssistant/Webhook → 直接通过
2. `{PLATFORM}_ALLOW_ALL_USERS=true` → 如 `TELEGRAM_ALLOW_ALL_USERS`
3. 如果是 bot 且 `{PLATFORM}_ALLOW_BOTS` → 通过
4. Pairing store (DM pairing approved list)
5. 平台白名单: `{PLATFORM}_ALLOWED_USERS`
6. 全局白名单: `GATEWAY_ALLOWED_USERS`
7. **如果没有任何 allowlist 配置**: 
   - `_adapter_enforces_own_access_policy()` — Telegram/WhatsApp 返回 False
   - **只有 WeCom/Weixin/Yuanbao/QQBot 返回 True**
   - Telegram 走不到这里 → fallback 到 `GATEWAY_ALLOW_ALL_USERS`
8. `GATEWAY_ALLOW_ALL_USERS=true` → 通过
9. 默认: **拒绝**

## Telegram DM 授权生效条件

必须满足以下至少一条：
- `TELEGRAM_ALLOW_ALL_USERS=true` 在 .env
- `GATEWAY_ALLOW_ALL_USERS=true` 在 .env
- `TELEGRAM_ALLOWED_USERS=<chat_id>` 在 .env

## 注意

- `config.yaml` 的 `allowed_chats` 只在 `_should_process_message` 中对**群聊**生效
- DM 完全不经过 `allowed_chats` 检查
- `enforces_own_access_policy` 是 adapter 属性，Telegram adapter 未设置
