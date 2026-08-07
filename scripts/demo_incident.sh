#!/usr/bin/env bash
# Demo: trigger ShortenerDown and show recovery (Incident Response evidence).
set -euo pipefail

BASE="${1:-http://localhost:8080}"
APP_TIER_STOPPED=0

restore_app_tier() {
  if [ "$APP_TIER_STOPPED" -eq 1 ]; then
    echo "Restoring app tier after interrupted demo..."
    docker compose start app1 app2 || true
    APP_TIER_STOPPED=0
  fi
}

trap restore_app_tier EXIT

echo "== 1. Baseline =="
curl -sf "$BASE/health" | head -c 80
echo

echo "== 2. Stop app tier (expect alerts within ~1 min) =="
docker compose stop app1 app2
APP_TIER_STOPPED=1

echo "Waiting 120s for Prometheus scrape, ShortenerDown (1m), and Alertmanager group_wait..."
sleep 120

echo "== 3. Check health (expect failure) =="
curl -sf "$BASE/health" && echo "unexpected success" || echo "health check failed as expected"

echo "== 4. Restart app tier =="
docker compose start app1 app2
APP_TIER_STOPPED=0
trap - EXIT
sleep 10

echo "== 5. Recovery =="
curl -sf "$BASE/health"
echo
echo "Done. Check Alertmanager http://localhost:9093 and your ALERT_WEBHOOK_URL channel."
