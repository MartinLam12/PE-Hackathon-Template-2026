"""Integration tests for pagination on GET /urls.

Before pagination existed the endpoint serialized every row in the table
on every request, which was the throughput bottleneck documented in
docs/performance.md. These tests pin the fix: a bounded default, a hard
ceiling a client cannot exceed, and a working offset.
"""

from datetime import datetime, timezone

from app.models.url import ShortURL
from app.routes.urls import DEFAULT_LIMIT, MAX_LIMIT


def _make_urls(count, start=0):
    now = datetime.now(timezone.utc)
    ShortURL.insert_many(
        [
            {
                "short_code": f"code{i:04d}",
                "original_url": f"https://example.com/{i}",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            for i in range(start, start + count)
        ]
    ).execute()


def test_defaults_to_bounded_page(client):
    """With no ?limit, the response is capped at DEFAULT_LIMIT rows, not the whole table."""
    _make_urls(DEFAULT_LIMIT + 25)

    response = client.get("/urls")

    assert response.status_code == 200
    assert len(response.get_json()) == DEFAULT_LIMIT


def test_explicit_limit_is_honoured(client):
    _make_urls(30)

    response = client.get("/urls?limit=5")

    assert response.status_code == 200
    assert len(response.get_json()) == 5


def test_limit_is_clamped_to_max(client):
    """A client asking for more than MAX_LIMIT cannot reopen the bottleneck."""
    _make_urls(MAX_LIMIT + 50)

    response = client.get(f"/urls?limit={MAX_LIMIT + 50}")

    assert response.status_code == 200
    assert len(response.get_json()) == MAX_LIMIT


def test_offset_pages_through_results(client):
    _make_urls(10)

    first = client.get("/urls?limit=4&offset=0").get_json()
    second = client.get("/urls?limit=4&offset=4").get_json()

    assert len(first) == 4
    assert len(second) == 4
    assert {u["short_code"] for u in first}.isdisjoint({u["short_code"] for u in second})


def test_offset_past_the_end_returns_empty_list(client):
    _make_urls(3)

    response = client.get("/urls?limit=10&offset=100")

    assert response.status_code == 200
    assert response.get_json() == []


def test_zero_limit_returns_400(client):
    response = client.get("/urls?limit=0")

    assert response.status_code == 400
    assert response.get_json()["error"] == "bad_request"


def test_negative_offset_returns_400(client):
    response = client.get("/urls?offset=-1")

    assert response.status_code == 400
    assert response.get_json()["error"] == "bad_request"


def test_non_integer_limit_returns_400(client):
    """Flask's type=int coerces a bad value to None, which must not 500."""
    response = client.get("/urls?limit=abc")

    assert response.status_code == 400
    assert response.get_json()["error"] == "bad_request"


def test_pagination_composes_with_user_id_filter(client):
    now = datetime.now(timezone.utc)
    for i in range(6):
        ShortURL.create(
            user_id=1 if i < 4 else 2,
            short_code=f"usr{i:03d}",
            original_url=f"https://example.com/{i}",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    response = client.get("/urls?user_id=1&limit=2")

    urls = response.get_json()
    assert len(urls) == 2
    assert all(u["user_id"] == 1 for u in urls)
