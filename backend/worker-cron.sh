#!/bin/sh
set -e

CRON_H=${TRACKING_CRON_HOUR:-16}
CRON_M=${TRACKING_CRON_MINUTE:-30}

# /etc/cron.d 格式需包含运行用户（root）
{
  echo "$CRON_M $CRON_H * * 1-5 root cd /app && python -m app.worker.run >> /var/log/worker.log 2>&1"
  echo ""
} > /etc/cron.d/tracking
chmod 0644 /etc/cron.d/tracking

echo "Worker cron: $CRON_H:$CRON_M Mon-Fri"
touch /var/log/worker.log

# 启动时先跑一次
python -m app.worker.run || true

cron -f
