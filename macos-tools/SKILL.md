---
name: macos-tools
description: Class-level umbrella for macOS-specific automation tools — iMessage, Notes, Reminders, FindMy, computer use, system profiling, and Mac Mini environment management.
category: devops
---

# macOS Tools & Automation

Umbrella for macOS-native tools and automation on the Mac Mini M4 production environment.

## Sub-Workflow Map

| Tool / Use Case | Reference |
|----------------|-----------|
| iMessage (send/receive via imsg CLI) | `references/imessage.md` |
| Apple Notes (CRUD via memo CLI) | `references/apple-notes.md` |
| Apple Reminders (via remindctl) | `references/apple-reminders.md` |
| FindMy (device/AirTag tracking) | `references/findmy.md` |
| macOS Computer Use (desktop drive) | `references/macos-computer-use.md` |
| Mac Mini environment (hardware + setup) | `references/mac-mini-environment.md` |
| System profiling (scan + inventory) | `references/mac-system-profiling.md` |
| Proxy bypass (Clash Verge/Surge) | `references/macos-proxy-bypass.md` |

## Common Pitfalls

- Most tools require macOS-specific CLIs (imsg, memo, remindctl)
- Computer Use requires active desktop session
- System profiling commands need absolute paths
- Mac Mini runs headless — some GUI-dependent tools may need workarounds
- **macOS 系统代理（Clash Verge/Surge）会劫持所有出站 TCP 连接**，见 `references/macos-proxy-bypass.md`