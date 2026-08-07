# Incident response runbooks

Step-by-step guides for alerts defined in [`monitoring/alert_rules.yml`](../monitoring/alert_rules.yml). Use with the Grafana dashboard **URL Shortener — Incident Response** and structured logs from `docker compose logs`.

---

## ShortenerDown (critical)

**Trigger:** Prometheus cannot scrape `/metrics` through nginx for 1 minute.

**What it means:** The load-balanced app is unreachable or not exporting metrics.

### Diagnose

1. Check Grafana **Scrape health** stat panel — should be `0`.
2. Run manual checks:
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/health
   curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/metrics
   docker compose ps
   ```
3. Inspect logs:
   ```bash
   docker compose logs --tail=100 nginx app1 app2
   ```

### Remediate

1. Restart failed containers: `docker compose restart app1 app2 nginx`
2. If Postgres is down, see [Database unavailable](#database-unavailable) in [failure-modes.md](failure-modes.md).
3. Confirm recovery: scrape health returns `1`, `/health` returns 200.

---

## HighErrorRate (warning)

**Trigger:** More than 5% of HTTP requests return 5xx for 2 minutes.

**What it means:** Application or database errors are affecting users.

### Diagnose

1. Open Grafana → **Error rate (5xx)** panel — note when the spike started.
2. Check **Response latency p95** — often rises with DB issues.
3. Search logs for 503/500:
   ```bash
   docker compose logs app1 app2 | rg "status=50"
   ```
4. Hit a failing route directly:
   ```bash
   curl -s http://localhost:8080/urls | head
   ```

### Remediate

1. If logs show `Database unavailable`, restart Postgres: `docker compose restart postgres`
2. If one app instance is bad, restart it: `docker compose restart app1`
3. Verify error rate drops in Grafana within 2–3 minutes.

---

## HighClientErrorRate (warning)

**Trigger:** More than 20% of requests return 4xx for 2 minutes.

**What it means:** Clients sending bad input or requesting missing short codes — usually not a server outage.

### Diagnose

1. Grafana **Request rate** — is traffic abnormal?
2. Sample a 404/400 from logs:
   ```bash
   docker compose logs app1 | rg "status=40"
   ```
3. Confirm API behaviour matches [failure-modes.md](failure-modes.md).

### Remediate

1. Usually no restart needed — document bad client or bad short codes.
2. If unexpected, check recent deploys and roll back if needed.

---

## HighAppCPU (warning)

**Trigger:** An `app1` or `app2` container exceeds ~75% of one CPU core for 2 minutes.

**What it means:** Load is high or a hot loop is burning CPU.

### Diagnose

1. Grafana **App CPU (containers)** — which instance?
2. Compare **Request rate** — organic load vs. runaway traffic.
3. Run load test history: see [performance.md](performance.md).

### Remediate

1. Scale horizontally: ensure both `app1` and `app2` are up behind nginx.
2. Enable/verify Redis cache (`REDIS_URL` set, `CACHE_DISABLED` unset).
3. If attack traffic, rate-limit at nginx or block source IPs.

---

## HighAppMemory (warning)

**Trigger:** App container RSS above ~400 MB for 2 minutes.

**What it means:** Memory pressure — possible leak or traffic spike.

### Diagnose

1. Grafana **App memory (containers)** panel.
2. `docker stats app1 app2` for live usage.
3. Check for large list queries without pagination limits.

### Remediate

1. Restart the affected container: `docker compose restart app1`
2. Review `GET /urls` pagination defaults in `app/routes/urls.py`.
3. Monitor memory after restart in Grafana.

---

## Health watch alerts (backup path)

If Prometheus is down, [`scripts/health_watch.py`](../scripts/health_watch.py) polls `/health` every 60 seconds and posts to `ALERT_WEBHOOK_URL` when unhealthy.

```bash
export ALERT_WEBHOOK_URL="https://discord.com/api/webhooks/..."
uv run python scripts/health_watch.py --url http://localhost:8080/health
```

Follow the same diagnose/remediate steps as **ShortenerDown**.

---

## Escalation

1. Check runbook for the firing alert (this file).
2. Use Grafana dashboard + logs to confirm root cause.
3. Apply remediate steps; wait one evaluation interval (2 min for most rules).
4. If still firing after 15 minutes, page the team lead and attach Grafana screenshot + `docker compose ps` output.
