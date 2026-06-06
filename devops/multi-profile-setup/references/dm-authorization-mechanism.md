# Hermes DM Authorization Mechanism

## 概览

新 profile 的 Telegram DM 被拒（`Unauthorized user`）的根因分析。

## 授权检查链（`gateway/run.py` → `_is_user_authorized`）

消息到达 gateway 后，`_is_user_authorized` 按以下顺序检查：

```
1. TELEGRAM_ALLOW_ALL_USERS=true?        → YES → 放行
2. TELEGRAM_ALLOWED_USERS 含 user_id?    → YES → 放行  
3. GATEWAY_ALLOWED_USERS 含 user_id?     → YES → 放行
4. pairing_store.is_approved?            → YES → 放行
5. _adapter_enforces_own_access_policy?  → YES → 放行
6. GATEWAY_ALLOW_ALL_USERS=true?         → YES → 放行
7. 默认 → 拒绝 (Unauthorized)
```

## 关键事实

### `_adapter_enforces_own_access_policy` 对 Telegram 返回 False

只有这些平台的 adapter 有此属性：WeCom, Weixin, Yuanbao, QQBot, WhatsApp。

Telegram adapter (`gateway/platforms/telegram.py`) **没有** `enforces_own_access_policy` 属性，因此第 5 步永远不触发。

### `allowed_chats` 不管 DM

`config.yaml` 的 `allowed_chats` 在 `_should_process_message`（`gateway/platforms/telegram.py:5081`）中处理，**只过滤群聊消息**：

```python
# telegram.py line 5103
if not self._is_group_chat(message):
    return True  # ← DM 直接放行，不检查 allowed_chats
```

所以设 `allowed_chats: '8447296166'` 对 DM Unauthorized 问题无效。

### 其他 profile 为什么能工作

其他三个 profile（default/her-m2/english-tutor）可能在某处设置了 `GATEWAY_ALLOW_ALL_USERS=true` 或 `TELEGRAM_ALLOW_ALL_USERS=8447296166`。新 profile 从 default 克隆配置和 .env 时，如果源 profile 的环境变量在 launchd plist 中（不在 .env 中），则不会被克隆。

## 修复方案

**方案 A（推荐 — 最简单）**：`.env` 中加 `GATEWAY_ALLOW_ALL_USERS=true`，重启 gateway。

**方案 B（精细控制）**：`.env` 中加 `TELEGRAM_ALLOWED_USERS=8447296166`，重启 gateway。只允许指定 chat_id。

## 源码位置

- 授权入口：`gateway/run.py:7361` — `_is_user_authorized(source)`
- 授权实现：`gateway/run.py:6949` — `def _is_user_authorized`
- Adapter 策略检查：`gateway/run.py:6925` — `_adapter_enforces_own_access_policy`
- Telegram 群聊过滤：`gateway/platforms/telegram.py:5081` — `_should_process_message`
- Config → env bridge：`gateway/config.py:1019-1023` — `allowed_chats → TELEGRAM_ALLOWED_CHATS`
