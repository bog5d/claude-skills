# TDAI Memory Gateway — Local Embedding Enablement

## Background
TencentDB Agent Memory Gateway ships with `LocalEmbeddingService` (node-llama-cpp + embeddinggemma-300m-Q8_0.gguf, ~300MB) but intentionally blocks it in the config parser. Three source patches + one config change are needed to enable it.

After enablement: `{"embeddingService": true}` in health check, semantic search replaces keyword-only search.

## Verification
```bash
# Health check
curl -s http://localhost:8420/health | python3 -m json.tool
# Expected: {"status":"ok","embeddingService":true}

# Check running state
launchctl list | grep memory
# Expected: PID column non-empty
```

## When gateway is down
```bash
# Check startup logs
cat ~/.hermes/logs/tdai-gateway.log | tail -20

# Common failure: launchd script syntax error
bash -n ~/.hermes/scripts/tdai-gateway.sh

# Restart
launchctl kickstart -k gui/501/ai.tdai.memory-gateway
```

## Patch Sources (3 files)

### 1. config.ts (line ~362) — unblock provider="local"
Path: `~/.memory-tencentdb/node_modules/@tencentdb-agent-memory/memory-tencentdb/src/config.ts`

Change from blocking to allowing local:
```typescript
// BEFORE:
} else if (embeddingProviderRaw === "local") {
    embeddingProvider = "none";
    embeddingEnabled = false;

// AFTER:
} else if (embeddingProviderRaw === "local") {
    embeddingProvider = "local";
    embeddingEnabled = true;
```

### 2. factory.ts (line ~94) — add local embedding creation branch
Path: `~/.memory-tencentdb/node_modules/@tencentdb-agent-memory/memory-tencentdb/src/core/store/factory.ts`

Add after the remote embedding if-block:
```typescript
} else if (config.embedding.enabled && config.embedding.provider === "local") {
    embeddingService = createEmbeddingService({
        provider: "local",
        modelPath: (config.embedding as any).modelPath,
        modelCacheDir: (config.embedding as any).modelCacheDir,
    }, logger);
}
```

### 3. gateway/config.ts (line ~138) — pass top-level config
Path: `~/.memory-tencentdb/node_modules/@tencentdb-agent-memory/memory-tencentdb/src/gateway/config.ts`

Change from:
```typescript
const memoryRaw = obj(fileConfig, "memory");
const memory = parseMemoryConfig(memoryRaw as ...);
```
To:
```typescript
const memory = parseMemoryConfig(fileConfig as ...);
```

## Config addition
In `~/.memory-tencentdb/tdai-gateway.yaml`, add at TOP level:
```yaml
embedding:
  enabled: true
  provider: "local"
```

## Automated script
Run `~/.memory-tencentdb/patch-local-embedding.sh` after npm reinstall to reapply all patches.

## Model details
- Model: `hf:ggml-org/embeddinggemma-300m-qat-q8_0-GGUF/embeddinggemma-300m-qat-Q8_0.gguf`
- Size: ~300MB (Q8_0 quantized)
- Engine: node-llama-cpp (CPU-only, no GPU required)
- First run: downloads from HuggingFace (~2-5 min, may be slow in mainland China)
