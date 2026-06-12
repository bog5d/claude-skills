---
name: telegram-action-buttons
description: "为 Hermes Agent 的 Telegram 响应附加快捷操作按钮（继续/重试/解释/修改），并在按钮被点击时合成 MessageEvent 注入 gateway 处理管道。适用于任何需要在 Telegram 消息后添加交互式 inline keyboard 的场景。"
category: software-development
---

# Telegram Action Buttons for Hermes Agent

## When to Use

当需要为 Telegram 响应附加交互式 inline keyboard 按钮时：
- "继续"按钮让用户一键触发 agent 继续工作
- "重试"按钮用不同方式重新执行
- "解释"按钮获取当前结果的说明
- 任何需要用户通过按钮触发预设操作而非打字输入的场景

## Architecture

```
send() 方法尾部
  └─ _should_attach_action_buttons() → 判断是否显示按钮
  └─ InlineKeyboardMarkup([...])    → 构建按钮布局
  └─ edit_message_reply_markup()     → 将按钮附加到已发送消息

_handle_callback_query()
  └─ act:action 解析
  └─ 构造合成 MessageEvent
  └─ asyncio.ensure_future(self._on_message(event)) → 注入 gateway
```

## Implementation

### Step 1: 在 send() 中附加按钮

在 `gateway/platforms/telegram.py` 的 `send()` 方法中，发送完所有 chunks 后、return 之前：

```python
message_ids.append(str(msg.message_id))

# ── Action buttons: attach inline keyboard to the last chunk ──
if message_ids and self._should_attach_action_buttons(content, metadata):
    last_msg_id = message_ids[-1]
    try:
        action_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("▶️ Continue", callback_data="act:continue"),
                InlineKeyboardButton("🔄 Retry", callback_data="act:retry"),
            ],
            [
                InlineKeyboardButton("💡 Explain", callback_data="act:explain"),
                InlineKeyboardButton("✏️ Revise", callback_data="act:revise"),
            ],
        ])
        await self._bot.edit_message_reply_markup(
            chat_id=int(chat_id),
            message_id=int(last_msg_id),
            reply_markup=action_keyboard,
        )
    except Exception:
        pass  # Non-fatal — buttons are a convenience
```

### Step 2: 条件判断方法

```python
@staticmethod
def _should_attach_action_buttons(content: str, metadata: dict = None) -> bool:
    if not content or not content.strip():
        return False
    # Skip pure MEDIA: references
    stripped = content.strip()
    if stripped.startswith("MEDIA:") and len(stripped) < 100:
        return False
    # Skip very short responses
    if len(stripped) < 20:
        return False
    # Skip if explicitly disabled via metadata
    if metadata and metadata.get("no_action_buttons"):
        return False
    return True
```

### Step 3: 在 callback handler 中处理按钮点击

在 `_handle_callback_query()` 中，找到 appropiate 的位置插入：

```python
# --- Action button callbacks (act:action) ---
if data.startswith("act:"):
    action = data.split(":", 1)[1] if ":" in data else ""
    if action not in ("continue", "retry", "explain", "revise"):
        await query.answer(text="Unknown action.")
        return

    # Map action to a synthetic user message
    action_prompts = {
        "continue": "/continue",
        "retry": "重试刚才的操作，换一种方式",
        "explain": "解释一下刚才做了什么，以及为什么这么做",
        "revise": "修改/优化刚才的结果",
    }
    prompt = action_prompts.get(action, action)

    await query.answer(text=f"⏳ Sending: {action}...")

    # Remove buttons from the original message
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Build source for synthetic event
    user = query.from_user
    source = self.build_source(
        chat_id=str(query.message.chat_id),
        chat_name=getattr(query.message.chat, "title", None) or getattr(query.message.chat, "full_name", None),
        chat_type="dm",
        user_id=str(user.id) if user else None,
        user_name=user.full_name if user else None,
    )

    # Create synthetic MessageEvent
    from gateway.platforms.base import MessageEvent, MessageType
    synthetic_event = MessageEvent(
        source=source,
        text=prompt,
        message_type=MessageType.TEXT,
        raw_message=query.message,
        reply_to=None,
    )

    # Inject into gateway pipeline
    import asyncio
    asyncio.ensure_future(self._on_message(synthetic_event))
    return
```

## Key Design Decisions

1. **`edit_message_reply_markup` 而不是在发送时传 `reply_markup`** — 因为消息可能被拆分为多个 chunk，只能在最后一个 chunk 上附加按钮。先发送全部 chunks，再编辑最后一条的 reply_markup
2. **synthetic MessageEvent 而不是直接调用 agent** — 让 gateway 的完整处理管道（授权检查、session 管理、速率限制）正常运作，而不是绕过它们
3. **`asyncio.ensure_future` 而不是 `await`** — callback handler 需要立即返回以响应 Telegram 的 callback query。消息处理在后台进行
4. **按钮点击后移除** — `edit_message_reply_markup(reply_markup=None)` 防止用户多次点击，也提供视觉反馈

## Pitfalls

1. **`_on_message` 必须已经绑定** — `hasattr(self, "_on_message")` 检查是必须的，否则在没有 gateway 的环境（如单独测试时）不会崩溃
2. **`build_source` 的 `chat_type`** — 按钮一般出现在 DM 中。如果是 group/thread，需要从 `query.message.chat` 中正确推断 type
3. **避免按钮与 exec_approval 冲突** — 如果消息已经用于 exec approval（`ea:` callback），不应再附加 action buttons。检查 content 中是否包含 approval 关键词
4. **callback_data 长度限制** — Telegram 限制 callback_data 最多 64 字节。`act:action` 格式（约 12-20 字节）完全在限制内
5. **Gate callback order in _handle_callback_query** — `act:` 处理必须在 `page:`（pager）之前、`update_prompt:` 之后，因为它们是不同优先级的交互模式
6. **动作提示语言** — `action_prompts` 使用中文，与 `/continue` 命令配合。如果 `/continue` 未注册为 slash command，gateway 会把它当作普通文本消息发送给 agent

## Verification

```bash
# 1. 语法检查
python3 -c "import py_compile; py_compile.compile('gateway/platforms/telegram.py', doraise=True); print('OK')"

# 2. 确认 callback_data 格式正确
python3 -c "
actions = ['act:continue', 'act:retry', 'act:explain', 'act:revise']
for a in actions:
    assert len(a.encode()) <= 64, f'{a} exceeds 64 byte limit'
    print(f'✅ {a} ({len(a.encode())} bytes)')
"

# 3. 确认 build_source 存在
python3 -c "
from gateway.platforms.telegram import TelegramAdapter
assert hasattr(TelegramAdapter, 'build_source')
print('✅ build_source method exists')
"
```
