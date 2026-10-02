#!/usr/bin/env bash
set -e

echo "[1/5] validating environment"
python scripts/validate_env.py || true

echo "[2/5] starting api"
echo "python scripts/start_api.py"

echo "[3/5] starting bot"
echo "python scripts/start_bot.py"

echo "[4/5] starting workers"
echo "python workers/matchmaking_worker.py"
echo "python workers/event_consumer_worker.py"
echo "python workers/notification_worker.py"

echo "[5/5] playtest stack ready"
