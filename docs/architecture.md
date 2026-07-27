# Architecture overview

High-level view of how requests move through the app and where errors are handled.

## System diagram

```mermaid
flowchart TB
    Client[Browser / API client] --> Gunicorn[Gunicorn WSGI]
    Gunicorn --> Flask[Flask create_app]
    Flask --> BeforeReq[before_request: db.connect]
    Flask --> Routes[Blueprints / routes]
    Routes --> Urls["/urls, /urls/code, /code redirect"]
    Routes --> Health["/health — no DB"]
    BeforeReq --> Postgres[(PostgreSQL)]
    Urls --> Postgres
    Flask --> ErrorHandlers["Error handlers in app/__init__.py"]
    ErrorHandlers --> JsonResponse["JSON 400 / 404 / 503 / 500"]
    Flask --> Teardown[teardown_appcontext: db.close]
```

## Key files

| File | Role |
|------|------|
| `run.py` | WSGI entry point (`gunicorn run:app`) |
| `app/__init__.py` | App factory + global error handlers |
| `app/database.py` | Postgres connection, per-request connect/close |
| `app/routes/urls.py` | URL CRUD and redirect routes |
| `tests/conftest.py` | SQLite test DB (no live Postgres needed) |

## Related docs

- [failure-modes.md](failure-modes.md) — what breaks, status codes, chaos/CI diagrams
- [coverage-gaps-for-person-1.md](coverage-gaps-for-person-1.md) — untested paths and suggested tests
