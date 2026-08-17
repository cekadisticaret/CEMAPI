#!/bin/bash
# Panel değişikliklerinden sonra tek komutla yeniden başlat.
set -e
cd "$(dirname "$0")/.."
if [ -f .env ]; then set -a; . ./.env; set +a; fi
PORT="${COPTC_PORT:-8080}"
pkill -f "web/dashboard.py" 2>/dev/null || true
sleep 1
nohup ./venv/bin/python web/dashboard.py >> /tmp/coptc_dashboard.log 2>&1 &
sleep 1
echo "Dashboard :$PORT — PID $(pgrep -f 'web/dashboard.py' | head -1)"
