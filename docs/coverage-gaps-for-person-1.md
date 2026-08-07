# Test coverage

Generated from `uv run pytest --cov=app --cov-report=term-missing`.

**44 tests, 100% coverage** — exceeds Reliability Silver (50%) and Gold (70%) targets.

| Module | Coverage |
|---|---|
| `app/*` | 100% |

## Suite layout

| Directory | Scope |
|---|---|
| `tests/unit/` | Model constraints, `/health`, cache config, ProxyFix |
| `tests/integration/` | Full HTTP stack: URLs, pagination, caching, errors, collisions, observability |

```bash
uv run pytest --cov=app --cov-report=term-missing
```

CI enforces `fail_under = 98` in `pyproject.toml`.
