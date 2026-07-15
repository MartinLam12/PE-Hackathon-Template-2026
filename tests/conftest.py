"""Shared pytest fixtures.

Provides a Flask app and test client backed by a throwaway SQLite
database instead of Postgres, so the suite runs without a live
database connection. `PostgresqlDatabase` is monkeypatched to return a
SQLite instance for the duration of each test; tables are created
before and dropped after.
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
    monkeypatch.setattr("app.database.PostgresqlDatabase", lambda *a, **k: test_db)

    application = create_app()
    application.config.update(TESTING=True)

    db.create_tables(MODELS)
    yield application

    db.drop_tables(MODELS)
    if not db.is_closed():
        db.close()


@pytest.fixture
def client(app):
    """Test client bound to the `app` fixture, for issuing requests without a live server."""
    return app.test_client()
