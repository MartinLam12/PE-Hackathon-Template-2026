"""Integration tests for short_code collision handling on POST /urls."""

from datetime import datetime, timezone

from app.models.url import ShortURL


def test_create_url_retries_after_short_code_collision(client, monkeypatch):
    """IntegrityError on duplicate code retries with a fresh code."""
    now = datetime.now(timezone.utc)
    ShortURL.create(
        short_code="dup001",
        original_url="https://example.com/taken",
        created_at=now,
        updated_at=now,
    )

    codes = iter(["dup001", "fresh1"])
    monkeypatch.setattr("app.routes.urls._new_code", lambda: next(codes))

    response = client.post("/urls", json={"original_url": "https://example.com/new"})
    assert response.status_code == 201
    assert response.get_json()["short_code"] == "fresh1"


def test_create_url_collision_exhaustion_returns_503(client, monkeypatch):
    """Five consecutive collisions return 503 instead of crashing."""
    now = datetime.now(timezone.utc)
    ShortURL.create(
        short_code="dupfix",
        original_url="https://example.com/taken",
        created_at=now,
        updated_at=now,
    )

    monkeypatch.setattr("app.routes.urls._new_code", lambda: "dupfix")

    response = client.post("/urls", json={"original_url": "https://example.com/new"})
    assert response.status_code == 503
    data = response.get_json()
    assert data["error"] == "service_unavailable"
    assert "unique" in data["message"].lower()
