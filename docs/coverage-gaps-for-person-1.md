# Coverage gaps for Person 1

Generated from `uv run pytest --cov=app --cov-report=term-missing` (96% overall).

## Coverage map

```mermaid
flowchart TB
    subgraph covered [Covered ~96%]
        Routes["app/routes/urls.py — list, create, get, redirect"]
        DbConnect["app/database.py — connect + before_request"]
        Handlers400["400 / 404 / 503 from routes"]
        Health["GET /health — skips DB even when connect fails"]
        OpError["OperationalError / ServiceUnavailable → 503"]
    end

    subgraph gaps [Needs tests — Person 1]
        G1["app/__init__.py — 500 catch-all handler"]
        G2["app/database.py — _db_close teardown"]
        G3["app/routes/urls.py — collision retry loop"]
    end

    covered --> gaps
```

## Untested paths

Please add tests for the following:

- **`app/__init__.py` — `handle_internal_server_error` (line 42)** — Catch-all 500 handler. Matters because unexpected exceptions must return JSON `{ "error": "internal_server_error" }`, not an HTML stack trace.

- **`app/database.py` — `_db_close` (line 38)** — Teardown closes the DB connection after each request. Matters for connection leaks under load or after errors.

- **`app/routes/urls.py` — `create_url` retry loop (lines 59–62)** — `IntegrityError` on duplicate `short_code` retries up to 5 times, then returns **503**. Matters because collision handling is a real failure mode under traffic.

## Suggested test approach

```mermaid
flowchart LR
    G1["500 handler"] --> T1["Raise RuntimeError in test route → expect 500 JSON"]
    G2["_db_close"] --> T2["Assert db.is_closed after request teardown"]
    G3["Collision loop"] --> T3["Mock _new_code to return duplicate → expect 503"]
```

Run coverage after adding tests:

```bash
uv run pytest --cov=app --cov-report=term-missing
```
