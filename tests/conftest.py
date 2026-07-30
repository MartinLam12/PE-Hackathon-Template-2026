"""Shared pytest fixtures.

Provides a Flask app and test client backed by a throwaway SQLite
database instead of Postgres, so the suite runs without a live
database connection. `PooledPostgresqlDatabase` is monkeypatched to
return a SQLite instance for the duration of each test; tables are
created before and dropped after.

The cache falls back to an in-process `SimpleCache` whenever `REDIS_URL`
is unset, so tests exercise the real caching code paths without needing
a Redis server.
"""

import pytest
from peewee import SqliteDatabase

from app import create_app
from app.database import db
from app.models import Event, ShortURL, User

MODELS = [User, ShortURL, Event]


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Flask app wired to a throwaway SQLite file instead of Postgres.

    A file (not :memory:) is required because the app opens/closes a
    connection on every request via before_request/teardown_appcontext,
    and an in-memory SQLite DB would lose its data between connections.
    """
    test_db = SqliteDatabase(str(tmp_path / "test.db"))
    monkeypatch.setattr("app.database.PooledPostgresqlDatabase", lambda *a, **k: test_db)
    # Force the SimpleCache backend even if the developer running the suite
    # has REDIS_URL exported for local Docker work.
    monkeypatch.delenv("REDIS_URL", raising=False)

    application = create_app()
    # DEBUG=False so the suite mirrors how the app actually runs under
    # gunicorn, rather than inheriting FLASK_DEBUG from a developer's local
    # .env. It matters: Flask-Caching re-raises backend errors in debug mode
    # and falls back to the database outside it, and the fallback is the
    # behaviour we depend on.
    application.config.update(TESTING=True, DEBUG=False)

    db.create_tables(MODELS)
    yield application

    db.drop_tables(MODELS)
    if not db.is_closed():
        db.close()


@pytest.fixture
def client(app):
    """Test client bound to the `app` fixture, for issuing requests without a live server."""
    return app.test_client()
