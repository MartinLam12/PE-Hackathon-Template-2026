"""Unit tests for cache backend selection in init_cache."""

from flask import Flask

from app.cache import init_cache


def test_init_cache_uses_simple_cache_by_default(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("CACHE_DISABLED", raising=False)

    app = Flask(__name__)
    init_cache(app)

    assert app.config["CACHE_TYPE"] == "SimpleCache"


def test_init_cache_uses_null_cache_when_disabled(monkeypatch):
    monkeypatch.setenv("CACHE_DISABLED", "1")
    monkeypatch.delenv("REDIS_URL", raising=False)

    app = Flask(__name__)
    init_cache(app)

    assert app.config["CACHE_TYPE"] == "NullCache"


def test_init_cache_uses_redis_when_url_set(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.delenv("CACHE_DISABLED", raising=False)

    app = Flask(__name__)
    init_cache(app)

    assert app.config["CACHE_TYPE"] == "RedisCache"
    assert app.config["CACHE_REDIS_URL"] == "redis://localhost:6379/0"
