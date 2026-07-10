# AIOS Flow Engine Dockerfile (V3)
# 多阶段：builder + runtime
# 启动两个进程：API (uvicorn :8081) + Temporal Worker
FROM python:3.11-slim AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.11-slim AS runtime
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

COPY src ./src
WORKDIR /app/src

ENV PYTHONUNBUFFERED=1
EXPOSE 8081

# 入口脚本：后台跑 worker + 前台跑 API
COPY <<'EOF' /entrypoint.sh
#!/bin/sh
set -e
echo "[entrypoint] starting temporal worker in background"
python -m aios_flow.worker &
WORKER_PID=$!
echo "[entrypoint] worker pid=$WORKER_PID, starting API"
trap "kill $WORKER_PID 2>/dev/null || true" TERM INT
exec uvicorn aios_flow.main:app --host 0.0.0.0 --port 8081
EOF
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
