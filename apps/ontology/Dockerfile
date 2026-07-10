# AIOS Ontology Dockerfile (V3)
# 多阶段：builder + runtime
FROM python:3.11-slim AS builder
WORKDIR /app

RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g; s|security.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
 && apt-get update && apt-get install -y --no-install-recommends \
    gcc \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
# V6 优化：BuildKit cache mount 持久 pip 缓存到 host + 国内 pip 源
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip wheel --wheel-dir /wheels . -i https://mirrors.aliyun.com/pypi/simple/

FROM python:3.11-slim AS runtime
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install /wheels/*.whl -i https://mirrors.aliyun.com/pypi/simple/ && rm -rf /wheels

COPY src ./src
WORKDIR /app/src

ENV PYTHONUNBUFFERED=1
EXPOSE 8083

CMD ["uvicorn", "aios_ontology.main:app", "--host", "0.0.0.0", "--port", "8083"]
