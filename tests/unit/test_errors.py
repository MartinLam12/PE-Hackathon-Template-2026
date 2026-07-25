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


def test_health_ok_without_database(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
