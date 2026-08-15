#!/bin/bash
# Panel değişikliklerinden sonra tek komutla yeniden başlat.
set -e
cd "$(dirname "$0")/.."
PORT="${COPTC_PORT:-8080}"
pkill -f "web/dashboard.py" 2>/dev/null || true
sleep 1
COPTC_PORT="$PORT" nohup ./venv/bin/python web/dashboard.py >> /tmp/coptc_dashboard.log 2>&1 &
sleep 1
echo "Dashboard :$PORT — PID $(pgrep -f 'web/dashboard.py' | head -1)"
