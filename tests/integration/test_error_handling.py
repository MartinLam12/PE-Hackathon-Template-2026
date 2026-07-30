"""Integration tests for error handling across the whole request stack.

Verifies that failures raised anywhere between routing, the database
layer, and the route handler are converted into the documented JSON
error shape by the handlers in `app/__init__.py` — never an HTML stack
trace. See docs/failure-modes.md for the matching failure catalogue.
"""

from datetime import datetime, timezone
from unittest.mock import patch

from peewee import OperationalError

from app.database import db
from app.models.url import ShortURL


def test_create_url_missing_body_returns_400(client):
    response = client.post("/urls", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "bad_request"
    assert "original_url" in data["message"]


def test_create_url_no_json_returns_400(client):
    response = client.post("/urls")
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "bad_request"


def test_get_unknown_url_returns_404(client):
    response = client.get("/urls/not-a-real-code")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "not_found"


def test_redirect_unknown_code_returns_404(client):
    response = client.get("/not-a-real-code")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "not_found"


def test_redirect_inactive_url_returns_404(client):
    now = datetime.now(timezone.utc)
    ShortURL.create(
        short_code="dead01",
        original_url="https://example.com",
        is_active=False,
        created_at=now,
        updated_at=now,
    )

    response = client.get("/dead01")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "not_found"


def test_database_unavailable_returns_503(client):
    with patch.object(db.obj, "connect", side_effect=OperationalError("connection refused")):
        response = client.get("/urls")
    assert response.status_code == 503
    data = response.get_json()
    assert data["error"] == "service_unavailable"


def test_query_time_database_error_returns_503(client):
    """An OperationalError raised mid-query must become a 503, not a stack trace."""
    with patch.object(
        ShortURL, "select", side_effect=OperationalError("server closed the connection")
    ):
        response = client.get("/urls")

    assert response.status_code == 503
    data = response.get_json()
    assert data["error"] == "service_unavailable"
    assert data["message"] == "Database unavailable"


def test_database_error_evicts_idle_pooled_connections(client):
    """A dead pooled connection must not be handed to the next request too.

    After Postgres restarts, pooled handles survive client-side but their
    server is gone. One failure has to purge the idle pool, or every stale
    connection costs its own failed request.
    """
    # Patch the underlying database, not the proxy: DatabaseProxy forwards
    # attribute access, so a patch applied to the proxy cannot be undone.
    with patch.object(db.obj, "close_idle", create=True) as close_idle, patch.object(
        ShortURL, "select", side_effect=OperationalError("server closed the connection")
    ):
        response = client.get("/urls")

    assert response.status_code == 503
    close_idle.assert_called_once()


def test_interface_error_is_also_handled(client):
    """psycopg2 reports an already-closed connection as InterfaceError."""
    from peewee import InterfaceError

    with patch.object(
        ShortURL, "select", side_effect=InterfaceError("connection already closed")
    ):
        response = client.get("/urls")

    assert response.status_code == 503
    assert response.get_json()["error"] == "service_unavailable"


def test_unexpected_exception_returns_json_500(app):
    """An unhandled error must still return the documented JSON shape."""
    # TESTING=True re-raises exceptions instead of routing them to the error
    # handlers, which is exactly the handler we want to exercise here.
    app.config.update(PROPAGATE_EXCEPTIONS=False)

    with patch.object(ShortURL, "select", side_effect=RuntimeError("boom")):
        response = app.test_client().get("/urls")

    assert response.status_code == 500
    data = response.get_json()
    assert data["error"] == "internal_server_error"
    assert data["message"] == "Internal server error"


def test_health_ok_without_database(client):
    with patch.object(db.obj, "connect", side_effect=OperationalError("connection refused")):
        response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
