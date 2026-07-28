# Holo-3.1 模型选择指南

## 核心认知

Holo-3.1 不是通用聊天模型，而是 **Computer-Use 专用模型**。

### 定位
- **开发者**：H Company（前 OpenAI 核心成员 Alex Birch, Alex Nichol, Alex Andonian）
- **发布时间**：2026年6月11日
- **核心能力**：看图理解屏幕 UI → 定位交互元素 → 执行操作（点击/打字/滚动）
- **基准表现**：OSWorld 50.6%, AndroidWorld 46.9%（超越 Gemini 2.5 Pro 和 Claude Sonnet 4.5）

### 适合场景
- ✅ 看图操作电脑（截图 → 分析 → 点击按钮/输入文字）
- ✅ 理解网页/App 界面布局
- ✅ 简单的桌面自动化任务
- ✅ 多模态交互（看图+文字指令）

### 不适合场景
- ❌ 深度推理（数学、逻辑、规划）
- ❌ 复杂编程（代码生成、调试、架构设计）
- ❌ 长文本创作（文章、报告、翻译）
- ❌ 专业领域问答（法律、金融、医疗）

### 部署方式
- **本地**：Ollama 运行 `mradermacher/Holo-3.1-4B-GGUF:Q4_K_M`，约 3GB 显存，~26 tok/s
- **云端**：Groq 免费 API，100 req/min，55 tok/s
- **Hermes 集成**：通过 custom provider 配置 base_url 指向本地 llama-server 或 Groq endpoint

### 与通用模型的对比

| 能力 | Holo-3.1 | 通用模型 (Claude/GPT/DeepSeek) |
|------|----------|-------------------------------|
| 看图操作 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 深度推理 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 代码生成 | ⭐ | ⭐⭐⭐⭐⭐ |
| 文本创作 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 响应速度 | 快 (26-55 tok/s) | 中等 (5-20 tok/s) |
| 成本 | 免费 (Groq) / 极低 (本地) | 按 token 计费 |

## 2026-06-17 配置案例

### 问题
holo-local profile 的 Telegram bot 不响应。

### 排查过程
1. **config.yaml 缩进错误** — `api_server` 块的 `enabled: false` 缩进不正确，导致 YAML 解析失败
2. **端口冲突** — api_server 默认 8642 端口被 default gateway 占用
3. **User ID 不匹配** — 配置允许的用户 ID 是 501（PID），但实际 Telegram User ID 是 8447296166

### 修复步骤
```bash
# 1. 修正 YAML 缩进
# 确保 api_server.enabled: false 正确嵌套

# 2. 禁用 api_server（避免端口冲突）
# 在 config.yaml 中设置 api_server.enabled: false

# 3. 更新允许的用户 ID
# 在 .env 中设置 TELEGRAM_ALLOWED_USERS=8447296166

# 4. 重启 gateway
launchctl kickstart -k gui/501/ai.hermes.gateway-holo-local
```

### 验证
```bash
# 确认 gateway 启动成功
tail ~/.hermes/profiles/holo-local/logs/gateway.log | grep "Telegram"

# 确认 Telegram 连接
# 日志中出现 "Connected via polling" 即成功

# 发送测试消息
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=8447296166&text=🟢 Holo-3.1 本地模型已上线"
```
