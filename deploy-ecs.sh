#!/usr/bin/env bash
# deploy-ecs.sh — 元冰可可 AIOS V4 部署脚本 (ECS Anolis 8)

set -e
cd /opt/ybkk

echo "=== [1/6] clone repo ==="
if [ ! -d ybkk ]; then
  git clone https://github.com/01men/ybkk.git
fi
cd ybkk
git config --global --add safe.directory /opt/ybkk/ybkk
git pull origin main 2>&1 | tail -3
echo "  HEAD: $(git rev-parse --short HEAD)"
echo "  version: $(grep -o 'AIOS_VERSION=.*' deploy/compose/.env.example 2>/dev/null || cat src/aios_common/__init__.py 2>/dev/null | grep -i version | head -1)"

echo "=== [2/6] write .env ==="
SECRET=$(date +%s | sha256sum | head -c 12)
cat > deploy/compose/.env <<EOF
AIOS_VERSION=0.4.0
AIOS_API_PORT=8000
AIOS_CONSOLE_PORT=3000

POSTGRES_DB=aios
POSTGRES_USER=aios
POSTGRES_PASSWORD=aios_${SECRET}_a
POSTGRES_HOST=postgres

NEO4J_AUTH=neo4j/aios_${SECRET}_n

MINIO_ROOT_USER=aios
MINIO_ROOT_PASSWORD=aios_${SECRET}_m

AIOS_OLLAMA_PULL_MODELS=qwen2.5:7b

GRAFANA_ADMIN_PASSWORD=aios_graf_${SECRET}
EOF
echo "  .env written"

echo "=== [3/6] compose pull + build (custom images) ==="
cd /opt/ybkk/ybkk/deploy/compose
docker compose pull --ignore-pull-failures 2>&1 | tail -10 || true
echo "  building ybkk-api..."
docker compose build api 2>&1 | tail -15
echo "  building ybkk-web..."
docker compose build web 2>&1 | tail -15
echo "  building ybkk-ingest..."
docker compose build ingest 2>&1 | tail -15
echo "  building ybkk-ontology..."
docker compose build ontology 2>&1 | tail -15
echo "  building ybkk-flow-engine..."
docker compose build flow-engine 2>&1 | tail -15
echo "  building ybkk-ollama..."
docker compose build ollama 2>&1 | tail -15

echo "=== [4/6] compose up -d ==="
docker compose up -d --remove-orphans 2>&1 | tail -30
sleep 8
docker compose ps

echo "=== [5/6] wait ollama pull qwen2.5:7b ==="
for i in $(seq 1 30); do
  if curl -sf http://localhost:11434/api/tags 2>/dev/null | grep -q "qwen2.5:7b"; then
    echo "  qwen2.5:7b ready after ${i}*30s"
    break
  fi
  echo "  waiting ollama... iter=$i"
  sleep 30
done
curl -sf http://localhost:11434/api/tags 2>&1 | head -c 400
echo ""

echo "=== [6/6] health checks ==="
echo "  --- api ---"
curl -sf -o /dev/null -w "    api http=%{http_code} time=%{time_total}s\n" http://localhost:8000/api/v1/health || echo "    api NOT responding"
echo "  --- web ---"
curl -sf -o /dev/null -w "    web http=%{http_code} time=%{time_total}s\n" http://localhost:3000/ || echo "    web NOT responding"
echo "  --- ollama ---"
curl -sf -o /dev/null -w "    ollama http=%{http_code} time=%{time_total}s\n" http://localhost:11434/api/tags || echo "    ollama NOT responding"
echo "  --- postgres ---"
docker compose exec -T postgres pg_isready -U aios 2>&1 | head -3 || echo "    pg NOT ready"
echo "  --- neo4j ---"
curl -sf -o /dev/null -w "    neo4j http=%{http_code}\n" http://localhost:7474/ || echo "    neo4j NOT responding"

echo "=== [done] deployment script finished ==="
docker compose ps
docker compose logs --tail=20 api 2>&1 | tail -20