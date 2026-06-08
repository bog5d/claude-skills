#!/bin/bash
# TDAI Memory Gateway launcher for launchd
# REFERENCE — copy to ~/.hermes/scripts/tdai-gateway.sh if corrupted
set -e

# Source Hermes .env for DEEPSEEK_API_KEY
if [ -f "$HOME/.hermes/.env" ]; then
  set -a; source "$HOME/.hermes/.env"; set +a
fi

# Source gateway-specific env
if [ -f "$HOME/.memory-tencentdb/tdai-gateway.env" ]; then
  set -a; source "$HOME/.memory-tencentdb/tdai-gateway.env"; set +a
fi

# Map DEEPSEEK_API_KEY -> TDAI_LLM_API_KEY
if [ -n "$DEEPSEEK_API_KEY" ]; then
  export TDAI_LLM_API_KEY="$DEEPSEEK_API_KEY"
else
  echo "FATAL: DEEPSEEK_API_KEY not found in env" >&2
  exit 1
fi

exec node --import tsx/esm \
  "$HOME/.memory-tencentdb/node_modules/@tencentdb-agent-memory/memory-tencentdb/src/gateway/server.ts"
