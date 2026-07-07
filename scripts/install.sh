#!/bin/bash
set -e
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then cp .env.example .env; echo "已创建 .env，请编辑后重新运行"; exit 0; fi
docker compose up -d --build
echo "荐迹已启动: http://localhost"
echo "演示用户 13888888888 / demo123456"
echo "管理员见 .env 中 ADMIN_PHONE / ADMIN_PASSWORD"
