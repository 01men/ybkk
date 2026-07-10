# AIOS Ontology Dockerfile (V3)
# 多阶段：builder + runtime
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
EXPOSE 8083

CMD ["uvicorn", "aios_ontology.main:app", "--host", "0.0.0.0", "--port", "8083"]
