---
name: tencentdb-agent-memory-integration
description: "TencentDB Agent Memory 四层记忆系统与 Hermes 集成——安装、配置、启动、共存架构。Phase 1-3 完整 SOP。"
category: devops
---

# TencentDB Agent Memory × Hermes 集成

## 架构

```
┌─────────────────────────────────────────────────┐
│                 Hermes Agent (Python)             │
│  ┌───────────────────────────────────────────┐   │
│  │  MemoryManager                            │   │
│  │  └─ memory_tencentdb provider (HTTP client)│   │
│  │       │ POST /recall, /capture, /search    │   │
│  └───────┼───────────────────────────────────┘   │
│          │                                        │
└──────────┼────────────────────────────────────────┘
           │  HTTP (127.0.0.1:8420)
┌──────────┼────────────────────────────────────────┐
│  TDAI Memory Gateway (Node.js)                    │
│  ┌───────┴───────────────────────────────────┐   │
│  │  L0 原始对话 → SQLite + JSONL              │   │
│  │  L1 原子事实 → LLM 提取 + BM25 索引        │   │
│  │  L2 场景聚类 → Markdown 文件               │   │
│  │  L3 用户画像 → persona.md                  │   │
│  │  Offload   → Mermaid 任务状态图 (可选)     │   │
│  └───────────────────────────────────────────┘   │
│  Storage: SQLite + sqlite-vec (~/.memory-tencentdb/)│
└───────────────────────────────────────────────────┘

与其他记忆系统共存：
  Agent Memory  → 「从对话中提取什么」(L1-L3 提取管道)
  EverOS        → 「怎么检索和关联」(混合检索)
  Mem0          → 「语义精排」(Rerank)
  Memory 工具   → 保持不变 (MEMORY.md 快速注入)
  Skills        → 「程序性记忆」不变
```

## 快速恢复 (Disaster Recovery)

### 症状判断

```bash
# Gateway 挂了的典型表现
curl -s http://localhost:8420/health   # 无响应 / connection refused
launchctl list | grep memory           # PID=0 或 exit code=2
```

### 标准恢复流程

```bash
# 1. 先检查启动脚本语法（常见：API key 变量名损坏）
bash -n ~/.hermes/scripts/tdai-gateway.sh || {
  echo "SCRIPT CORRUPTED — restore from skill reference:"
  echo "  tencentdb-agent-memory-integration/references/tdai-gateway.sh"
  exit 1
}

# 2. 杀掉残留进程（如果有）
lsof -ti :8420 | xargs kill 2>/dev/null; sleep 1

# 3. 手动启动诊断（写脚本 /tmp/test-gw.sh 再用 bash 执行）
#    因为 Hermes 阻止 foreground terminal 里使用 & 和 source
cat > /tmp/test-gw.sh << 'SCRIPT'
#!/bin/bash
cd ~/.memory-tencentdb
source ~/.hermes/.env 2>/dev/null
lsof -ti :8420 | xargs kill 2>/dev/null || true
sleep 1
node --import tsx/esm \
  node_modules/@tencentdb-agent-memory/memory-tencentdb/src/gateway/server.ts \
  > /tmp/tdai-gw.log 2>&1 &
GW_PID=$!
sleep 6
cat /tmp/tdai-gw.log
curl -s http://localhost:8420/health
kill $GW_PID 2>/dev/null || true
SCRIPT
bash /tmp/test-gw.sh

# 4. 修完后重启为 launchd 管理
launchctl kickstart -k gui/501/ai.tdai.memory-gateway
# 验证
sleep 4
launchctl list | grep memory
curl -s http://localhost:8420/health | python3 -m json.tool
```

### 常见崩溃原因

| exit code | 可能原因 | 修法 |
|-----------|---------|------|
| 2 | 模块加载失败 / 配置语法错误 / 端口占用 | 手动启动看日志 |
| 0 + PID=0 | KeepAlive 未触发（SuccessfulExit 不重启） | `launchctl kickstart -k` |
| -9 (SIGKILL) | 进程被强制杀死 → macOS 内存压力 OOM 或 launchd 超时 | 检查 `gateway.error.log` 中的 `SIGTERM`→超时→`SIGKILL` 链；扩容 memory_char_limit；重启后注入上下文 |

### 注意

- `launchd` 的 stderr 不记录到系统日志，必须手动运行才能看到错误
- 不要用 `&` 在 foreground terminal 里后台化（被 Hermes 阻止）。写脚本 `/tmp/test-gw.sh` 再用 `bash /tmp/test-gw.sh` 执行
- 本 Gateway (`ai.tdai.memory-gateway`) 与 Hermes Gateway (`ai.hermes.gateway`) 是不同的 launchd 服务，互不影响

## 安装记录

### 已部署组件

| 组件 | 位置 | 状态 |
|------|------|------|
| npm 包 | `~/.memory-tencentdb/` | ✅ |
| Hermes 插件 | `~/.hermes/hermes-agent/plugins/memory/memory_tencentdb/` (symlink) | ✅ |
| Gateway 进程 | `localhost:8420` | ✅ |
| launchd 服务 | `~/Library/LaunchAgents/ai.tdai.memory-gateway.plist` | ✅ |
| 启动脚本 | `~/.hermes/scripts/tdai-gateway.sh` | ✅ |
| 环境变量 | `~/.memory-tencentdb/tdai-gateway.env` | ✅ |
| Gateway 配置 | `~/.memory-tencentdb/tdai-gateway.yaml` | ✅ |
| 数据目录 | `~/.memory-tencentdb/memory-tdai/` | ✅ |

### Hermes config.yaml 关键配置

```yaml
memory:
  provider: memory_tencentdb   # ← 从 mem0 切换
  memory_enabled: true
  user_profile_enabled: true
```

### 使用的 API

- **LLM**: DeepSeek API (deepseek-chat)
- **Embedding**: 本地 embeddinggemma-300m (待启用，当前纯 BM25 关键词检索)
- **成本**: 预估 ¥1-3/月 (L1/L2/L3 提取)

## Embedding 服务

### 是什么

把文字转成向量（Float32Array）的服务。Gateway 默认用纯 BM25 关键词检索（`strategy: "hybrid"` 实际退化为 keyword-only）。启用 embedding 后支持语义搜索：搜「编程风格」能匹配「反冗长主义」。

### 架构

Gateway 内 `factory.ts` 创建 embedding 服务，`config.ts` 解析配置。支持三种模式：

| 模式 | provider 值 | 依赖 | 可用 |
|------|-------------|------|------|
| 远程 OpenAI-compatible | 任何非 `"local"` 值 | `apiKey` + `baseUrl` + `model` + `dimensions` | ✅ 代码完整 |
| 本地 node-llama-cpp | `"local"` | `node-llama-cpp` + `embeddinggemma-300m` GGUF (~300MB) | ⚠️ 代码完整但被配置层封死 |
| 禁用 | `"none"` | 无 | ✅ 当前状态 |

### 启用本地 Embedding（需要撬开三层防护）

TencentDB 故意在配置管道中封死了 `provider: "local"`，虽然 `LocalEmbeddingService` 代码完整。启用需要修三个文件：

**第一层 — config.ts（`~/.memory-tencentdb/node_modules/@tencentdb-agent-memory/memory-tencentdb/src/config.ts`）**：
```typescript
// 第 362-368 行：将 provider="local" 强制改写为 "none"
// 修改前：
} else if (embeddingProviderRaw === "local") {
    embeddingProvider = "none";
    embeddingEnabled = false;
// 修改后：
} else if (embeddingProviderRaw === "local") {
    embeddingProvider = "local";
    embeddingEnabled = true;
```

**第二层 — factory.ts（同目录 `src/core/store/factory.ts`）**：
```typescript
// 第 94 行：只为远程 provider 创建 embeddingService
// 修改：新增 else-if 分支
} else if (config.embedding.enabled && config.embedding.provider === "local") {
    embeddingService = createEmbeddingService({
        provider: "local",
        modelPath: (config.embedding as any).modelPath,
        modelCacheDir: (config.embedding as any).modelCacheDir,
    }, logger);
}
```

**第三层 — gateway/config.ts（同目录 `src/gateway/config.ts`）**：
```typescript
// 第 138 行：parseMemoryConfig 只接收 fileConfig.memory 子树
// 需要确保 embedding 配置在 memory 子树中，或修改此处传递方式
const memoryRaw = obj(fileConfig, "memory");
```

**yaml 配置**（`~/.memory-tencentdb/tdai-gateway.yaml`）：
```yaml
# embedding 放在顶层，与 server/data/offload 同级（NOT 嵌套在 memory: 下）
# 因为 gateway/config.ts 已改为传 fileConfig 顶层给 parseMemoryConfig
embedding:
  enabled: true
  provider: "local"
```

### 完整修复流程（已验证通过，2026-06-08）

**全部三层已撬开，`embeddingService: true` 已确认。**

总体步骤（5 个修改点）：

**① yaml 配置** — `tdai-gateway.yaml` 顶层添加：
```yaml
embedding:
  enabled: true
  provider: "local"
```
注意：embedding 放顶层（与 offload/recall/pipeline 同级），NOT 嵌套在 `memory:` 下。

**② config.ts 放行 local** — 将 `provider: "local"` 的处理从「强制改写为 none」改为「放行」：
```diff
 } else if (embeddingProviderRaw === "local") {
-    embeddingProvider = "none";
-    embeddingEnabled = false;
-    embeddingConfigError = "...";
+    embeddingProvider = "local";
+    embeddingEnabled = true;
```

**③ factory.ts 补本地分支** — 在远程 embedding 条件后新增 else-if：
```typescript
} else if (config.embedding.enabled && config.embedding.provider === "local") {
    embeddingService = createEmbeddingService({
        provider: "local",
        modelPath: (config.embedding as any).modelPath,
        modelCacheDir: (config.embedding as any).modelCacheDir,
    }, logger);
}
```

**④ gateway/config.ts 传顶层配置** — 将 `parseMemoryConfig` 的入参从 `fileConfig.memory` 改为 `fileConfig`：
```diff
-  const memoryRaw = obj(fileConfig, "memory");
-  const memory = parseMemoryConfig(memoryRaw as ...);
+  const memory = parseMemoryConfig(fileConfig as Record<string, unknown> | undefined);
```
根因：`parseMemoryConfig` 读 `c.embedding`，但之前只传 `fileConfig.memory`（yaml 中为 `undefined`），导致 embedding 段丢失。传顶层 `fileConfig` 后 `c.embedding` 能正确读到。

**⑤ 修复 launchd 启动脚本** — `~/.hermes/scripts/tdai-gateway.sh` 曾因 API key 变量名被截断导致 shell 语法错误（`$DEEPSEEK_API_KEY` 被写成 `$DEE...`），Gateway 永远无法通过 launchd 启动。完整脚本见下文「launchd 启动脚本修复」。

### 验证

```bash
# 手动测试
lsof -ti :8420 | xargs kill 2>/dev/null; sleep 1
cd ~/.memory-tencentdb && bash /tmp/test-gw.sh
# 日志应显示:
#   [embedding] Using local embedding (node-llama-cpp, model=embeddinggemma-300m...)
#   embedding=enabled, provider=local

# Health 应返回 embeddingService: true
curl -s http://localhost:8420/health
# {"status":"ok","stores":{"vectorStore":true,"embeddingService":true}}

# launchd 启动
launchctl kickstart -k gui/501/ai.tdai.memory-gateway
```

## 坑与经验

### 启动与崩溃

1. **TDAI_LLM_* vs MEMORY_TENCENTDB_LLM_***：Gateway 本身读 `TDAI_LLM_*` 环境变量。Hermes 插件读 `MEMORY_TENCENTDB_LLM_*`。两者需要同时设置或在启动脚本中映射。

2. **Standalone Gateway ≠ OpenClaw Plugin**：Standalone 模式只支持 capture/recall/search；offload (Mermaid) 是 OpenClaw 插件功能。

3. **Docker 不是必需的**：原生 Node.js + npm 在本机直接跑，零 Docker 依赖。

4. **config.yaml 修改受网关保护**：必须用 `hermes config set` 而非直接文件写入。

5. **launchd 环境**：wrapper 脚本需同时 source `.hermes/.env` 和 `tdai-gateway.env`。plist 用 `KeepAlive.SuccessfulExit=false` + `ThrottleInterval=10` 确保 crash 自动重启。

6. **数据持久性**：Gateway 重启后数据不丢失（SQLite 存储在 `~/.memory-tencentdb/memory-tdai/`）。

7. **同 session 多 capture 触发管道**：默认每 5 轮触发一次（`everyNConversations: 5`），warmup 加速初始提取。

8. **memory_char_limit**：从默认 2200 上调至 5000，避免截断 Agent Memory 的 ~3000-5000 字符画像。

9. **launchd 看不到错误日志**：见下方「快速恢复」标准流程。必须用 `/tmp/test-gw.sh` 脚本手动运行看真实错误。恢复脚本模板：`references/tdai-gateway.sh`。

10. **跨 Profile 共享**（用户确认）：所有 Profile 共用同一 Gateway + 数据目录。L3 Persona 全局可见。english-tutor 也会召回技术画像，这是设计选择——用户选择"全 Profile 用 Agent Memory，接受共享"。

11. **Gateway 不重启的真正原因 — `lsof` 清端口**：`launchctl kickstart -k` 有时不生效（进程已僵死）。必须先用 `lsof -ti :8420 | xargs kill` 释放端口，再重新 load。

12. **launchd 看不到错误日志**：Gateway 的 stderr 不进入系统日志。crash 时 exit code 只能看到 2，需要手动运行 `node --import tsx/esm ...` 看真实错误。

13. **embedding 被故意封死**：`config.ts` 第 362-368 行硬编码将 `provider: "local"` 改写为 `"none"`。`factory.ts` 第 94 行只为远程 provider 创建 embedding 服务。需同时修两处 + 配好 yaml 才能启用本地 embedding。

14. **yaml 配置层级陷阱**：`parseMemoryConfig()` 读取 `c.embedding`、`c.pipeline` 等字段。之前代码只传 `fileConfig.memory`，导致顶层 `offload/recall/pipeline/embedding` 均未被读取（全用默认值）。修改 `gateway/config.ts` 传 `fileConfig` 顶层后修复。embedding 应放在 yaml 顶层（与 server/data/offload 同级），而非嵌套在 `memory:` 下。

15. **本地 embedding 模型**：`embeddinggemma-300m` GGUF (~300MB)，首次启动 `node-llama-cpp` 自动从 HuggingFace 下载。大陆网络可能需要代理。模型名：`hf:ggml-org/embeddinggemma-300m-qat-q8_0-GGUF/embeddinggemma-300m-qat-Q8_0.gguf`。

16. **launchd 启动脚本易损坏**：`tdai-gateway.sh` 第 16 行的 `$DEEPSEEK_API_KEY` 变量名可能被工具截断/损坏（变成 `$DEE...`），导致 shell 语法错误。症状：`launchctl list` 显示 PID=0 且 exit code=2，日志文件里全是 `unexpected EOF`。用 `bash -n ~/.hermes/scripts/tdai-gateway.sh` 检查语法。完整脚本模板见 `references/tdai-gateway.sh`。

### Profile 内存配置

17. **memory_char_limit 按 Profile 独立配置**：每个 Hermes profile 有自己的 `memory_char_limit`（在 `~/.hermes/profiles/<name>/config.yaml` 中）。default=5000 但其他 profile 可能只有 2200。过小的 limit 导致每次记忆写入都在边界反复替换，浪费 token 并引发级联错误。

18. **诊断 memory_char_limit 不足**：日志中出现 `Memory at 2,180/2,200 chars. Adding this entry would exceed the limit` → 立即扩容到 5000。修改 `~/.hermes/profiles/<name>/config.yaml` 中 `memory.memory_char_limit` 和 `memory.user_char_limit`（建议 3000）。

### Hermes Gateway SIGKILL 诊断

19. **SIGKILL (-9) exit code**：`launchctl list` 显示 exit code -9 表示进程被强制杀死。常见原因：macOS 内存压力（OOM）→ 系统发送 SIGKILL；或 launchd 超时后强制终止。日志中最后一条通常是 `Shutdown context: signal=SIGTERM`（先收到 SIGTERM，超时后 SIGKILL）。

20. **Gateway 重启后注入上下文**：Gateway 重启后 context 全空。通过 profile-scoped one-shot cron 注入唤醒提示：
```bash
cronjob action=create profile=<profile_name> schedule=<ISO_timestamp> repeat=1
prompt="你刚因 <原因> 重启。之前在做 <任务>。请查 memory 系统恢复上下文并汇报。"
```

21. **跨 Profile Gateway 区别**：`ai.tdai.memory-gateway`（TencentDB）和 `ai.hermes.gateway` / `ai.hermes.gateway-her-m2`（Hermes Gateway）是不同的 launchd 服务，互不影响。一个挂不影响另一个。

22. **kickstart vs bootout**：用 `launchctl kickstart -k gui/501/<label>` 重启 Hermes Gateway（不卸载服务定义）。不要用 `bootout`（会完全移除服务，导致后续 load 失败）。TDAI Gateway 可以用 `bootout` + `load`（无自保限制）。

### 自动化补丁

23. **npm 重装后重新打补丁**：本地 embedding 需要修改 3 个源文件。已有自动化脚本：`~/.memory-tencentdb/patch-local-embedding.sh`。执行 `bash ~/.memory-tencentdb/patch-local-embedding.sh` 即可一键复原所有 patch。详细流程见 `tdai-local-embedding` skill（当该 skill 存在时加载）。

## 运维

### 备份
- 手动：`bash ~/.hermes/scripts/backup-tdai-memory.sh`
- Cron：每日 03:00 自动备份（job `46b7f802c037`），保留最近 7 份
- 位置：`~/.hermes/backups/tdai-memory/`

### 健康巡检
- Cron：每 6 小时检测 Gateway（job `3a23bebc959b`），宕机告警

## 测试验证

```bash
# 健康检查（关注 embeddingService 字段）
curl http://localhost:8420/health
# 正常: {"status":"ok","stores":{"vectorStore":true,"embeddingService":true}}
# 降级: {"status":"ok","stores":{"vectorStore":true,"embeddingService":false}}

# Capture 对话
curl -X POST http://localhost:8420/capture \
  -H "Content-Type: application/json" \
  -d '{"session_key":"test","user_content":"...","assistant_content":"..."}'

# Recall 记忆 (跨 session 生效)
curl -X POST http://localhost:8420/recall \
  -H "Content-Type: application/json" \
  -d '{"query":"用户偏好","session_key":"any-session"}'
```
