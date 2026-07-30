"""Cache configuration.

Backed by Redis when `REDIS_URL` is set, and by an in-process
`SimpleCache` otherwise, so local runs and the test suite work without a
Redis server. Redis is what makes the multi-instance setup work: `app1`
and `app2` share one cache, so a value cached by one is a hit on the
other.

Routes use Flask-Caching's `@cache.cached` decorator directly. It already
does read-through and, outside debug mode, already falls back to calling
the view when the backend raises — so a Redis outage costs latency, not
availability. There is no hand-rolled wrapper here on purpose.

Hit rates come from Redis itself:

    docker compose exec redis redis-cli INFO stats | grep keyspace
"""

import os

from flask_caching import Cache

cache = Cache()


def init_cache(app):
    """Attach the cache to `app`, choosing a backend from the environment."""
    if os.environ.get("CACHE_DISABLED", "").lower() in {"1", "true", "yes"}:
        # NullCache reads always miss and writes go nowhere, so every request
        # falls through to Postgres. Lets the load test measure the same build
        # with and without caching — see docs/performance.md.
        config = {"CACHE_TYPE": "NullCache"}
    elif os.environ.get("REDIS_URL"):
        config = {
            "CACHE_TYPE": "RedisCache",
            "CACHE_REDIS_URL": os.environ["REDIS_URL"],
        }
    else:
        config = {"CACHE_TYPE": "SimpleCache"}

    config["CACHE_DEFAULT_TIMEOUT"] = int(os.environ.get("CACHE_TTL", 300))
    config["CACHE_KEY_PREFIX"] = "shortener:"

    app.config.from_mapping(config)
    cache.init_app(app)
