#!/bin/bash
# aios-ollama-entrypoint.sh —— V3 OPS-V3-02 自动 pull 模型
#
# 启动流程：
#   1. 后台启动 ollama serve
#   2. 轮询 ollama API 等待就绪（最多 60s）
#   3. 遍历 AIOS_OLLAMA_PULL_MODELS（逗号分隔），逐个 pull
#   4. 打印 success log；前台 wait ollama serve

set -e

LOG_PREFIX="[aios-ollama]"

# 后台启 ollama
echo "$LOG_PREFIX starting ollama serve in background"
ollama serve &
OLLAMA_PID=$!

# 等待就绪
echo "$LOG_PREFIX waiting for ollama to be ready (max 60s)..."
READY=0
for i in $(seq 1 60); do
  if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    READY=1
    echo "$LOG_PREFIX ollama ready after ${i}s"
    break
  fi
  sleep 1
done

if [ "$READY" -ne 1 ]; then
  echo "$LOG_PREFIX ERROR: ollama not ready after 60s, models NOT pulled"
  kill $OLLAMA_PID 2>/dev/null || true
  exit 1
fi

# Pull 默认模型
IFS=',' read -ra MODELS <<< "${AIOS_OLLAMA_PULL_MODELS:-qwen2.5:7b}"
for model in "${MODELS[@]}"; do
  model=$(echo "$model" | xargs)  # trim
  if [ -z "$model" ]; then continue; fi
  echo "$LOG_PREFIX pulling model: $model"
  if ollama pull "$model"; then
    echo "$LOG_PREFIX model pulled successfully: $model"
  else
    echo "$LOG_PREFIX WARNING: failed to pull $model (continuing)"
  fi
done

echo "$LOG_PREFIX all models ready. ollama serving on :11434"
wait $OLLAMA_PID
