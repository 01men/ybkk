# AIOS API 后端 Dockerfile (V6 - simplified)
# 单阶段：直接源码运行，避免 wheel 装到 site-packages/src/ 的路径错乱
FROM python:3.11-slim

WORKDIR /app

# V6: 国内 apt 源 + BuildKit cache mount + 国内 pip 源
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g; s|security.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
 && apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 装依赖（不靠 wheel，直接装到 site-packages；源码用 COPY 引入）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ \
        "fastapi>=0.115.0" \
        "uvicorn[standard]>=0.32.0" \
        "pydantic>=2.9.0" \
        "pydantic-settings>=2.6.0" \
        "sqlalchemy>=2.0.36" \
        "alembic>=1.14.0" \
        "asyncpg>=0.30.0" \
        "psycopg2-binary>=2.9.10" \
        "neo4j>=5.26.0" \
        "redis>=5.2.0" \
        "minio>=7.2.8" \
        "httpx>=0.27.2" \
        "pyjwt>=2.9.0" \
        "cryptography>=43.0.0" \
        "python-multipart>=0.0.20" \
        "pandas>=2.2.3" \
        "openpyxl>=3.1.5" \
        "sqlglot>=26.0.0" \
        "temporalio>=1.10.0" \
        "nats-py>=2.10.0" \
        "aiosqlite>=0.20.0"

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
EXPOSE 8000

# V6: 直接 copy 源码 + alembic.ini
COPY src ./src
COPY alembic.ini ./alembic.ini

# CMD: 先 migration，再 init admin，最后起 uvicorn
CMD ["sh", "-c", "alembic upgrade head && cd /app/src && python setup_default_admin.py 2>/dev/null; cd /app/src && uvicorn main:app --host 0.0.0.0 --port 8000"]