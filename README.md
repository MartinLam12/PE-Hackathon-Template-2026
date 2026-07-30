# MLH PE Hackathon — Flask + Peewee + PostgreSQL Template

A minimal hackathon starter template. You get the scaffolding and database wiring — you build the models, routes, and CSV loading logic.

**Stack:** Flask · Peewee ORM · PostgreSQL · uv

## **Important**

You need to work with around the seed files that you can find in [MLH PE Hackathon](https://mlh-pe-hackathon.com) platform. This will help you build the schema for the database and have some data to do some testing and submit your project for judging. If you need help with this, reach out on Discord or on the Q&A tab on the platform.

## Prerequisites

- **uv** — a fast Python package manager that handles Python versions, virtual environments, and dependencies automatically.
  Install it with:
  ```bash
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
  For other methods see the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/).
- PostgreSQL running locally (you can use Docker or a local instance)

## uv Basics

`uv` manages your Python version, virtual environment, and dependencies automatically — no manual `python -m venv` needed.

| Command | What it does |
|---------|--------------|
| `uv sync` | Install all dependencies (creates `.venv` automatically) |
| `uv run <script>` | Run a script using the project's virtual environment |
| `uv add <package>` | Add a new dependency |
| `uv remove <package>` | Remove a dependency |

## Quick Start

```bash
# 1. Clone the repo
git clone <repo-url> && cd mlh-pe-hackathon

# 2. Install dependencies
uv sync

# 3. Create the database
createdb hackathon_db

# 4. Configure environment
cp .env.example .env   # edit if your DB credentials differ

# 5. Seed the database
uv run seed.py

# 6. Run the server
uv run run.py

# 7. Verify
curl http://localhost:5000/health
# → {"status":"ok"}
```

## Project Structure

```
mlh-pe-hackathon/
├── app/
│   ├── __init__.py          # App factory (create_app) + error handlers
│   ├── cache.py             # Cache backend selection (Redis / in-process)
│   ├── database.py          # Pooled Postgres connection, per-request hooks
│   ├── models/              # User, URL, and event models
│   └── routes/
│       ├── __init__.py      # register_routes() — add blueprints here
│       └── urls.py          # URL CRUD, redirect, pagination
├── tests/
│   ├── unit/                # One layer in isolation
│   └── integration/         # Full request → route → DB → response
├── loadtest/
│   ├── locustfile.py        # Three load profiles + pass/fail thresholds
│   └── results/             # Committed CSV/HTML evidence per tier
├── chaos/
│   ├── chaos_test.sh        # Four fault-injection scenarios
│   └── results/             # Committed run transcript
├── docs/                    # Architecture, performance, failure modes
├── docker-compose.yml       # 2 app instances + Nginx + Postgres + Redis
├── nginx.conf               # Load balancing and failover
├── Dockerfile               # App image
├── .dockerignore            # Keeps .env and local state out of the image
├── .env.example             # Configuration template
├── pyproject.toml           # Project metadata + dependencies
├── run.py                   # Entry point: uv run run.py
└── seed.py                  # Load seed_data/ CSVs into Postgres
```

## URL endpoints

| Method | Path | Notes |
|---|---|---|
| `POST` | `/urls` | Create a short URL. Body: `{"original_url": "...", "title": "...", "user_id": 1}` — only `original_url` is required. Returns `201`. |
| `GET` | `/urls` | List URLs. Paginated: `?limit=` (default 50, max 200), `?offset=` (default 0). Optional `?user_id=`. |
| `GET` | `/urls/<short_code>` | URL details, or `404`. |
| `GET` | `/<short_code>` | `302` redirect to the original URL, or `404` if unknown or inactive. |
| `GET` | `/health` | `{"status":"ok"}`. Never touches the database, so it stays `200` during a database outage. |

`GET /urls` is capped at 200 rows per request — it used to return the whole table, which was the throughput bottleneck fixed for Gold. A `limit` above the ceiling is clamped rather than rejected; a non-integer or out-of-range `limit`/`offset` returns `400`.

The seed loader reads `seed_data/` by default. Set `SEED_DIR` to use another directory.

## How to Add a Model

1. Create a file in `app/models/`, e.g. `app/models/product.py`:

```python
from peewee import CharField, DecimalField, IntegerField

from app.database import BaseModel


class Product(BaseModel):
    name = CharField()
    category = CharField()
    price = DecimalField(decimal_places=2)
    stock = IntegerField()
```

2. Import it in `app/models/__init__.py`:

```python
from app.models.product import Product
```

3. Create the table (run once in a Python shell or a setup script):

```python
from app.database import db
from app.models.product import Product

db.create_tables([Product])
```

## How to Add Routes

1. Create a blueprint in `app/routes/`, e.g. `app/routes/products.py`:

```python
from flask import Blueprint, jsonify
from playhouse.shortcuts import model_to_dict

from app.models.product import Product

products_bp = Blueprint("products", __name__)


@products_bp.route("/products")
def list_products():
    products = Product.select()
    return jsonify([model_to_dict(p) for p in products])
```

2. Register it in `app/routes/__init__.py`:

```python
def register_routes(app):
    from app.routes.products import products_bp
    app.register_blueprint(products_bp)
```

## How to Load CSV Data

```python
import csv
from peewee import chunked
from app.database import db
from app.models.product import Product

def load_csv(filepath):
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    with db.atomic():
        for batch in chunked(rows, 100):
            Product.insert_many(batch).execute()
```

## Useful Peewee Patterns

```python
from peewee import fn
from playhouse.shortcuts import model_to_dict

# Select all
products = Product.select()

# Filter
cheap = Product.select().where(Product.price < 10)

# Get by ID
p = Product.get_by_id(1)

# Create
Product.create(name="Widget", category="Tools", price=9.99, stock=50)

# Convert to dict (great for JSON responses)
model_to_dict(p)

# Aggregations
avg_price = Product.select(fn.AVG(Product.price)).scalar()
total = Product.select(fn.SUM(Product.stock)).scalar()

# Group by
from peewee import fn
query = (Product
         .select(Product.category, fn.COUNT(Product.id).alias("count"))
         .group_by(Product.category))
```

## Error handling

All API errors return JSON with this shape:

```json
{ "error": "<code>", "message": "<human-readable detail>" }
```

| Status | When | Example |
|--------|------|---------|
| **400** | Invalid input | POST `/urls` without `original_url` |
| **404** | Short code not found or inactive | GET `/urls/badcode`, GET `/badcode` |
| **503** | Database unavailable or cannot allocate a unique code | DB down, repeated `short_code` collisions |
| **500** | Unexpected server error | Unhandled exception |

Handlers live in `app/__init__.py` (`BadRequest`, `NotFound`, `ServiceUnavailable`, `OperationalError`, `InternalServerError`). Routes call `abort(status, description=...)` so errors never crash into HTML stack traces.

`/health` skips the database connection, so it returns `{"status":"ok"}` even when Postgres is down.

A `503` can also mean the pooled database connection we were handed was dead (for example, Postgres restarted underneath us). The error handler evicts idle pooled connections when that happens, so the next request reconnects instead of drawing another dead handle.

See [docs/failure-modes.md](docs/failure-modes.md) for what can break, what users see, and how each case was tested. See [docs/architecture.md](docs/architecture.md) for system diagrams, and [docs/performance.md](docs/performance.md) for the bottleneck analysis.

## Scaling and load testing

`docker compose up` runs two app instances (`app1`, `app2`) behind an Nginx reverse proxy/load balancer (`nginx.conf`) on port 8080, sharing one Postgres instance and one Redis cache.

```
client -> nginx :8080 -> app1 :5000 -+
                      -> app2 :5000 -+-> postgres  +  redis
```

Measured with Locust ([loadtest/](loadtest/), raw results in [loadtest/results/](loadtest/results/)):

| | Users | Topology | Throughput | p95 | Errors |
|---|---|---|---|---|---|
| Bronze | 50 | 1 instance | 101 req/s | 14 ms | 0% |
| Silver | 200 | 2 instances + LB | 371 req/s | 110 ms | 0% |
| **Gold** | **500** | **2 instances + LB + Redis** | **960 req/s** | **15 ms** | **0%** |

With think time removed the stack sustained **3,132 req/s with zero failures**. At that point the app containers were at ~347% CPU while Postgres sat under 10% — the ceiling is application CPU, not the database.

Two changes did the work:

- **Pagination on `GET /urls`.** It previously returned every row in the table on every request. A default response went from ~422 KB to 10.7 KB — 40x smaller, and the largest single win.
- **Redis caching** on the redirect and detail routes, shared by both instances so a value cached by one is a hit on the other. **99.8% hit rate**, worth ~20% throughput and 24% off p95 — measured against the same build with `CACHE_DISABLED=1`.

Full analysis, including the two bugs the testing uncovered, is in [docs/performance.md](docs/performance.md).

## Caching

| Path | Cached | TTL |
|---|---|---|
| `GET /<short_code>` | the 302 response | 300 s |
| `GET /urls/<short_code>` | the JSON response | 60 s |
| `GET /urls` | not cached — always fresh | — |

Routes use Flask-Caching's `@cache.cached` decorator. Set `REDIS_URL` to use Redis; leave it unset and the app falls back to an in-process cache, which is what the test suite runs on. Set `CACHE_DISABLED=1` to bypass caching entirely.

The cache is an optimisation, never a source of truth: if Redis is unreachable, reads fall through to Postgres and the service stays correct, just slower. Tested in `tests/integration/test_caching.py` and verified by chaos Scenario D.

Hit rate comes from Redis itself:

```bash
docker compose exec redis redis-cli INFO stats | grep keyspace
```

## Chaos testing

[chaos/chaos_test.sh](chaos/chaos_test.sh) injects four faults against the running stack and records what happened. Committed transcript: [chaos/results/chaos-run.log](chaos/results/chaos-run.log).

| Scenario | Fault | Result |
|---|---|---|
| A | Kill the gunicorn master in `app1` | Docker restarted it (~5s); **41/41 requests through the LB succeeded** |
| B | Stop Postgres | `503` JSON on DB routes, `/health` stayed `200`, no crash, recovered in ~2s |
| C | Kill a gunicorn worker | Master respawned it; **39/39 requests succeeded** |
| D | Stop Redis | Redirect, list, detail and create all still served; **18/18 requests succeeded** |

See [docs/failure-modes.md](docs/failure-modes.md) for the full failure catalogue.

## Tests

```bash
uv run pytest --cov=app --cov-report=term-missing
```

The suite is split by scope:

| Directory | Scope | What it covers |
|---|---|---|
| `tests/unit/` | One layer in isolation | `ShortURL` model defaults and constraints (no HTTP); `/health` payload (no DB) |
| `tests/integration/` | Full request → route → DB → response | URL create/list/get/redirect round-trips; every documented error path (400/404/503) end-to-end |

Both suites share `tests/conftest.py`, which swaps Postgres for a throwaway SQLite file so no live database is needed.

Current coverage: **96%** (roadmap targets are 50% for Silver, 70% for Gold). Remaining uncovered lines are catalogued in [docs/coverage-gaps-for-person-1.md](docs/coverage-gaps-for-person-1.md).

## CI

GitHub Actions runs tests on every push and pull request (`.github/workflows/ci.yml`). Tests use an SQLite database via `tests/conftest.py`, so no live Postgres is required in CI.

**Failing tests block deployment.** Branch protection is enabled on `main` with the **test** check required and "strict" (branches must be up to date) turned on, so a red CI run cannot be merged into the branch that deploys.

```bash
# Verify the gate is live:
gh api repos/<owner>/<repo>/branches/main/protection --jq '.required_status_checks'
# → {"strict": true, "contexts": ["test"], ...}
```

## Tips

- Use `model_to_dict` from `playhouse.shortcuts` to convert model instances to dictionaries for JSON responses.
- Wrap bulk inserts in `db.atomic()` for transactional safety and performance.
- The template uses `teardown_appcontext` for connection cleanup, so connections are closed even when requests fail.
- Check `.env.example` for all available configuration options.
