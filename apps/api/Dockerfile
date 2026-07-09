# AIOS API 后端 Dockerfile (V1)
# 多阶段：builder + runtime
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 先 copy pyproject 装依赖（cache 友好）
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.11-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# 跑 migration + 启动 uvicorn
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

COPY src ./src
WORKDIR /app/src

CMD ["sh", "-c", "alembic upgrade head && python -m aios_api.setup_default_admin 2>/dev/null; uvicorn aios_api.main:app --host 0.0.0.0 --port 8000"]
