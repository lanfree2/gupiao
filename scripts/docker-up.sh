#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit SECRET_KEY and passwords before production."
fi

docker compose up -d --build
echo ""
echo "嘉岭佰已启动: http://localhost"
echo "API 文档:   http://localhost:8000/docs"
echo "演示账号:   13888888888 / demo123456"
echo "管理后台:   http://localhost/admin/login"
