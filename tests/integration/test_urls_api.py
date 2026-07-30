"""Integration tests for the URL API.

Each test drives a full request/response cycle — HTTP request through
Flask routing, into the route handler, out to the database via Peewee,
and back as JSON — rather than exercising a single layer in isolation.
"""

from datetime import datetime, timezone

from app.models.url import ShortURL


def test_list_urls_empty(client):
    response = client.get("/urls")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_and_get_url(client):
    response = client.post(
        "/urls",
        json={"original_url": "https://example.com", "title": "Example"},
    )
    assert response.status_code == 201
    created = response.get_json()
    assert created["original_url"] == "https://example.com"
    assert created["title"] == "Example"
    assert len(created["short_code"]) == 6

    response = client.get(f"/urls/{created['short_code']}")
    assert response.status_code == 200
    assert response.get_json()["short_code"] == created["short_code"]


def test_redirect_active_url(client):
    now = datetime.now(timezone.utc)
    ShortURL.create(
        short_code="go2ex",
        original_url="https://example.com/target",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    response = client.get("/go2ex", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] == "https://example.com/target"


def test_list_urls_filter_by_user_id(client):
    now = datetime.now(timezone.utc)
    ShortURL.create(
        user_id=1,
        short_code="usr001",
        original_url="https://example.com/1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    ShortURL.create(
        user_id=2,
        short_code="usr002",
        original_url="https://example.com/2",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    response = client.get("/urls?user_id=1")
    assert response.status_code == 200
    urls = response.get_json()
    assert len(urls) == 1
    assert urls[0]["user_id"] == 1
