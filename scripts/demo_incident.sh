#!/usr/bin/env bash
# Demo: trigger ShortenerDown and show recovery (Incident Response evidence).
set -euo pipefail

BASE="${1:-http://localhost:8080}"

echo "== 1. Baseline =="
curl -sf "$BASE/health" | head -c 80
echo

echo "== 2. Stop app tier (expect alerts within ~1 min) =="
docker compose stop app1 app2

echo "Waiting 75s for Prometheus + health-watch alerts..."
sleep 75

echo "== 3. Check health (expect failure) =="
curl -sf "$BASE/health" && echo "unexpected success" || echo "health check failed as expected"

echo "== 4. Restart app tier =="
docker compose start app1 app2
sleep 10

echo "== 5. Recovery =="
curl -sf "$BASE/health"
echo
echo "Done. Check Alertmanager http://localhost:9093 and your ALERT_WEBHOOK_URL channel."
