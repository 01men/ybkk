# AIOS API 后端 Dockerfile (V6 - hatchling wheel 模式)
# 标准多阶段：builder 出 wheel，runtime 装 wheel + 起 uvicorn
FROM python:3.11-slim AS builder

WORKDIR /app

RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g; s|security.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
 && apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src

# V6 优化：BuildKit cache mount 持久 pip 缓存到 host + 国内 pip 源
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip wheel --wheel-dir /wheels . -i https://mirrors.aliyun.com/pypi/simple/

FROM python:3.11-slim AS runtime

WORKDIR /app

RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g; s|security.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
 && apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install /wheels/*.whl -i https://mirrors.aliyun.com/pypi/simple/ --no-deps --no-index && \
    pip install -i https://mirrors.aliyun.com/pypi/simple/ \
        "fastapi>=0.115.0" "uvicorn[standard]>=0.32.0" "pydantic>=2.9.0" \
        "pydantic-settings>=2.6.0" "sqlalchemy>=2.0.36" "alembic>=1.14.0" \
        "asyncpg>=0.30.0" "psycopg2-binary>=2.9.10" "neo4j>=5.26.0" \
        "redis>=5.2.0" "minio>=7.2.8" "httpx>=0.27.2" "pyjwt>=2.9.0" \
        "cryptography>=43.0.0" "python-multipart>=0.0.20" \
        "pandas>=2.2.3" "openpyxl>=3.1.5" "sqlglot>=26.0.0" \
        "temporalio>=1.10.0" "nats-py>=2.10.0" "aiosqlite>=0.20.0" && \
    rm -rf /wheels

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# alembic.ini 必须和源码一起（alembic 跑 migrations 时需要）
COPY alembic.ini ./alembic.ini
COPY src ./src

# CMD: 先 alembic upgrade，再 init admin，最后 uvicorn
# uvicorn 启动 src.main:app（hatchling 把 src 装成 'src' 包）
CMD ["sh", "-c", "alembic upgrade head && cd /app/src && python setup_default_admin.py 2>/dev/null; cd /app/src && uvicorn main:app --host 0.0.0.0 --port 8000"]