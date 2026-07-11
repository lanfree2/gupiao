#!/usr/bin/env bash
# 在 Linux 服务器上执行：修复 HTTPS（Caddy + Docker 8080）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DOMAIN="${1:-carlingbuy.com}"

echo "==> 1. 拉取最新代码"
git fetch origin main
git reset --hard origin/main

echo "==> 2. 启动 Docker（web 监听 127.0.0.1:8080）"
docker compose up -d --build

echo "==> 3. 等待 API"
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
    echo "API OK"
    break
  fi
  sleep 2
  if [ "$i" -eq 30 ]; then
    echo "API 未就绪，查看日志："
    docker compose logs --tail=50 api
    exit 1
  fi
done

echo "==> 4. 检查本机 8080"
curl -fsS -o /dev/null http://127.0.0.1:8080/ || {
  echo "本机 8080 无响应"
  docker compose ps
  exit 1
}
echo "Web 8080 OK"

if ! command -v caddy >/dev/null 2>&1; then
  echo "未安装 Caddy，请先执行 docs/DEPLOY.md 第 6 节安装"
  exit 1
fi

echo "==> 5. 写入 Caddyfile"
sudo tee /etc/caddy/Caddyfile >/dev/null <<EOF
${DOMAIN}, www.${DOMAIN} {
    reverse_proxy localhost:8080
}
EOF

echo "==> 6. 启动 Caddy"
sudo systemctl enable caddy
sudo systemctl restart caddy
sleep 2
sudo systemctl status caddy --no-pager || true

echo "==> 7. 测试 HTTPS"
curl -fsS -o /dev/null "https://${DOMAIN}/" && echo "HTTPS OK: https://${DOMAIN}/" || {
  echo "HTTPS 暂不可用，查看 Caddy 日志："
  sudo journalctl -u caddy -n 30 --no-pager
  exit 1
}

echo ""
echo "完成。请确认 .env 中："
echo "CORS_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}"
echo "然后执行: docker compose restart api"
