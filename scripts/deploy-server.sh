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

echo "==> Waiting for API health (8000)..."
api_ok=0
for i in $(seq 1 40); do
  if curl -fsS --max-time 8 http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
    echo "OK: API is healthy"
    api_ok=1
    break
  fi
  sleep 3
done
if [ "$api_ok" -ne 1 ]; then
  echo "FAIL: API did not become healthy in time"
  docker compose logs --tail=80 api || true
  exit 1
fi

echo "==> Waiting for web (8080)..."
web_ok=0
for i in $(seq 1 30); do
  if curl -fsS --max-time 8 -o /dev/null http://127.0.0.1:8080/ 2>/dev/null; then
    echo "OK: web is healthy"
    web_ok=1
    break
  fi
  sleep 2
done
if [ "$web_ok" -ne 1 ]; then
  echo "WARN: web :8080 not ready yet"
fi

if command -v caddy >/dev/null 2>&1 && [ -f /etc/caddy/Caddyfile ]; then
  sudo -n systemctl restart caddy 2>/dev/null || sudo systemctl restart caddy 2>/dev/null || echo "WARN: could not restart Caddy"
fi

docker compose ps || true
echo "Deploy successful"
exit 0
