"""Integration tests for cached routes.

These run against the SimpleCache fallback (no Redis needed) but exercise
the same `@cache.cached` behaviour Redis uses in production: read-through
on the redirect and detail routes, no caching of 404s, and — the property
we actually depend on — falling back to the database when the cache
backend raises.
"""

from datetime import datetime, timezone
from unittest.mock import patch

from cachelib import SimpleCache
from redis.exceptions import ConnectionError as RedisConnectionError

from app.models.url import ShortURL


def _make_url(short_code="cache1", original_url="https://example.com/target", active=True):
    now = datetime.now(timezone.utc)
    return ShortURL.create(
        short_code=short_code,
        original_url=original_url,
        is_active=active,
        created_at=now,
        updated_at=now,
    )


def test_redirect_is_served_from_cache_on_second_request(client):
    """The second redirect for a code must not touch the database at all."""
    _make_url(short_code="hot001", original_url="https://example.com/hot")

    first = client.get("/hot001", follow_redirects=False)
    assert first.status_code == 302
    assert first.headers["Location"] == "https://example.com/hot"

    with patch.object(ShortURL, "get_or_none", side_effect=AssertionError("DB was hit")):
        second = client.get("/hot001", follow_redirects=False)

    assert second.status_code == 302
    assert second.headers["Location"] == "https://example.com/hot"


def test_detail_lookup_is_cached(client):
    _make_url(short_code="det001", original_url="https://example.com/detail")

    assert client.get("/urls/det001").status_code == 200

    with patch.object(ShortURL, "get_or_none", side_effect=AssertionError("DB was hit")):
        second = client.get("/urls/det001")

    assert second.status_code == 200
    assert second.get_json()["short_code"] == "det001"


def test_distinct_codes_get_distinct_cache_entries(client):
    """One code's cached response must never be served for another."""
    _make_url(short_code="aaa001", original_url="https://example.com/a")
    _make_url(short_code="bbb002", original_url="https://example.com/b")

    first = client.get("/aaa001", follow_redirects=False)
    second = client.get("/bbb002", follow_redirects=False)

    assert first.headers["Location"] == "https://example.com/a"
    assert second.headers["Location"] == "https://example.com/b"


def test_missing_code_is_not_cached(client):
    """A 404 must not be cached, or a code created later would stay missing."""
    assert client.get("/nope01", follow_redirects=False).status_code == 404

    _make_url(short_code="nope01", original_url="https://example.com/later")

    assert client.get("/nope01", follow_redirects=False).status_code == 302


def test_list_reflects_writes_immediately(client):
    """GET /urls is deliberately uncached, so a create shows up at once."""
    _make_url(short_code="lst001")

    before = client.get("/urls?limit=50").get_json()
    assert len(before) == 1

    assert client.post("/urls", json={"original_url": "https://example.com/new"}).status_code == 201

    after = client.get("/urls?limit=50").get_json()
    assert len(after) == 2


def test_cache_outage_degrades_to_the_database(client):
    """A dead cache must mean slower responses, not failed ones.

    `@cache.cached` swallows backend errors and calls the view instead.
    This pins that behaviour: if it ever changed, a Redis blip would turn
    into a site-wide 500 and we would want the test to say so.
    """
    _make_url(short_code="deg001", original_url="https://example.com/degraded")

    with patch.object(
        SimpleCache, "get", side_effect=RedisConnectionError("redis is down")
    ), patch.object(
        SimpleCache, "set", side_effect=RedisConnectionError("redis is down")
    ):
        redirect_response = client.get("/deg001", follow_redirects=False)
        detail_response = client.get("/urls/deg001")
        list_response = client.get("/urls")

    assert redirect_response.status_code == 302
    assert redirect_response.headers["Location"] == "https://example.com/degraded"
    assert detail_response.status_code == 200
    assert list_response.status_code == 200
    assert len(list_response.get_json()) == 1
