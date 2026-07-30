# Load testing

Load tests are written with [Locust](https://locust.io/) in [loadtest/locustfile.py](../loadtest/locustfile.py). Each simulated user hits `/health`, `GET /urls`, `POST /urls`, and follows the resulting short-code redirect.

## Bronze — baseline (single instance)

Single Flask instance (`app1`), run directly via gunicorn, no load balancer.

```bash
docker compose up -d postgres app1
uv run locust -f loadtest/locustfile.py --host http://localhost:5001 \
  --headless -u 50 -r 10 --run-time 45s
```

**Result:** 50 concurrent users, 4343 requests, **0 failures (0% error rate)**.

| Metric | Value |
|---|---|
| Median response time | 6 ms |
| p95 response time | 14 ms |
| p99 response time | 24 ms |
| Max response time | 36 ms |
| Throughput | ~101 req/s |

## Silver — scaled (2 instances + load balancer)

Two Flask instances (`app1`, `app2`) behind an Nginx reverse proxy/load balancer ([nginx.conf](../nginx.conf)), all started with a single `docker compose up`.

```bash
docker compose up -d
uv run locust -f loadtest/locustfile.py --host http://localhost:8080 \
  --headless -u 200 -r 20 --run-time 60s
```

**Result:** 200 concurrent users, 21905 requests, **0 failures (0% error rate)**.

| Metric | Value |
|---|---|
| Median response time | 15 ms |
| p95 response time | 110 ms |
| p99 response time | 180 ms |
| Max response time | 285 ms |
| Throughput | ~371 req/s |

Max response time (285 ms) is well under the 3-second target.

**Evidence of multiple instances (`docker compose ps`):**

```
NAME                                     SERVICE    PORTS
pe-hackathon-template-2026-app1-1        app1       0.0.0.0:5001->5000/tcp
pe-hackathon-template-2026-app2-1        app2       5000/tcp (internal only)
pe-hackathon-template-2026-nginx-1       nginx      0.0.0.0:8080->80/tcp
pe-hackathon-template-2026-postgres-1    postgres   5432/tcp (internal only)
```

**Evidence traffic is actually distributed:** `nginx.conf` adds an `X-Upstream-Addr` response header identifying which backend served each request. Spaced-out requests through `http://localhost:8080` alternate between the two container IPs:

```
X-Upstream-Addr: 172.20.0.4:5000
X-Upstream-Addr: 172.20.0.3:5000
X-Upstream-Addr: 172.20.0.4:5000
X-Upstream-Addr: 172.20.0.3:5000
```

## Scaling approach

`app1` and `app2` are two separate Docker Compose services built from the same [Dockerfile](../Dockerfile), each running the Flask app under gunicorn (2 workers) and sharing the same Postgres instance. Nginx (`nginx.conf`) is configured with an `upstream` block listing both containers and load-balances between them with its default round-robin algorithm. Only Nginx's port (8080) needs to be exposed externally — client traffic never talks to `app1`/`app2` directly in the scaled setup.
