# Load testing

Load tests are written with [Locust](https://locust.io/) in [loadtest/locustfile.py](../loadtest/locustfile.py). Raw results — CSVs and Locust's HTML reports — are committed under [loadtest/results/](../loadtest/results/).

Three workloads live in the locustfile:

| Class | Think time | Purpose |
|---|---|---|
| `ShortenerUser` | 0.1–1 s | The original mixed workload. Unchanged since Bronze so the tier-over-tier numbers compare like with like. |
| `RealisticUser` | 0.1–1 s | Read-heavy (90% redirects on existing codes), which is how a URL shortener is actually used. Used for the cache A/B. |
| `SaturationUser` | none | `RealisticUser` with think time removed, to find the actual ceiling. |

For the Gold bottleneck analysis and the cache A/B, see [performance.md](performance.md).

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

## Gold — optimized (2 instances + load balancer + Redis)

Same `ShortenerUser` workload as Bronze and Silver, at 500 concurrent users, against the fully optimized stack: pagination on `GET /urls`, Redis caching, and pooled database connections.

```bash
docker compose up -d
docker compose exec -T app1 uv run seed.py
# Wait until `docker compose ps` shows both app1 and app2 healthy first.
uv run locust -f loadtest/locustfile.py ShortenerUser --host http://localhost:8080 \
  --headless -u 500 -r 50 --run-time 60s \
  --csv loadtest/results/gold --html loadtest/results/gold.html
```

**Result:** 500 concurrent users, 56,712 requests, **0 failures**, against a 5% ceiling.

| Metric | Value |
|---|---|
| Median response time | 2 ms |
| p95 response time | 15 ms |
| Throughput | ~960 req/s |

Per endpoint:

| Endpoint | Requests | Failures | p95 | Avg size |
|---|---|---|---|---|
| `GET /health` | 24,227 | 0 | 14 ms | 16 B |
| `GET /urls` | 16,254 | 0 | 18 ms | 10,732 B |
| `GET /<short_code>` | 8,113 | 0 | 12 ms | 245 B |
| `POST /urls` | 8,118 | 0 | 19 ms | 222 B |

### Tier comparison

| | Bronze | Silver | Gold |
|---|---|---|---|
| Users | 50 | 200 | 500 |
| Throughput | 101 req/s | 371 req/s | **960 req/s** |
| p95 | 14 ms | 110 ms | **15 ms** |
| Error rate | 0% | 0% | **0%** |

Gold serves 2.5x Silver's concurrency at 2.6x the throughput with p95 7x lower. Most of that came from paginating `GET /urls`, whose default response shrank from ~422 KB to 10.7 KB — see [performance.md](performance.md).

### Pass/fail thresholds

Every run is checked when it finishes and exits non-zero if it missed:

- error rate under 5%, **per endpoint as well as overall**
- p95 under 500 ms

The per-endpoint check exists because an aggregate hid a real bug: 400 failing POSTs among 173,000 requests is 0.23% overall while 11% of POSTs were failing. Details in [performance.md](performance.md#two-bugs-the-testing-found).

### Beyond 500 users

With think time removed and 4 Locust processes, the stack sustained **3,132 req/s with 0 failures** (p95 130 ms). At that point the two app containers were using ~347% CPU while Postgres sat under 10%: the ceiling is application CPU, not the database. Caching is worth ~20% throughput here — measured against the same build with `CACHE_DISABLED=1`. Full analysis in [performance.md](performance.md).

## Scaling approach

`app1` and `app2` are two separate Docker Compose services built from the same [Dockerfile](../Dockerfile), each running the Flask app under gunicorn and sharing one Postgres instance and one Redis instance. Nginx (`nginx.conf`) is configured with an `upstream` block listing both containers and load-balances between them with its default round-robin algorithm. Only Nginx's port (8080) needs to be exposed externally — client traffic never talks to `app1`/`app2` directly in the scaled setup.

Changes made for Gold:

- **Workers.** 2 sync workers per instance meant an instance could handle only 2 concurrent requests. Now 4 `gthread` workers x 8 threads, because the work is I/O bound (Postgres and Redis round trips).
- **Shared cache.** Both instances point at one Redis, so a value cached by `app1` is a hit on `app2`. A per-instance in-memory cache would halve the hit rate.
- **Connection pooling.** Instances reuse Postgres connections rather than dialling one per request. `max_connections` is per worker *process*, so the ceiling is `instances x workers x max_connections` — 64 here, against a Postgres configured for 150.
- **Upstream health.** `max_fails=2 fail_timeout=10s` ejects a dead instance from the pool, and `proxy_next_upstream` retries idempotent requests against the survivor. Chaos testing confirms a killed instance costs zero failed requests ([failure-modes.md](failure-modes.md)).
