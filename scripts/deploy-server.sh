#!/usr/bin/env bash
# 在 Linux 服务器上手动执行，或与 GitHub Actions 部署脚本保持一致。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Pull latest main"
git fetch origin main
git reset --hard origin/main

echo "==> Rebuild and restart containers"
docker compose up -d --build

echo "==> Health check"
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/api/health >/dev/null; then
    echo "OK: API is healthy"
    docker compose ps
    exit 0
  fi
  sleep 3
done

echo "FAIL: API did not become healthy in time"
docker compose logs --tail=80 api
exit 1
