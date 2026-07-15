"""Unit tests for the ShortURL model's field-level behavior.

Exercises model defaults and constraints directly against the
database layer, without going through Flask routing or view logic.
"""

from datetime import datetime, timezone

import pytest
from peewee import IntegrityError

from app.models.url import ShortURL


def _now():
    """UTC timestamp helper for populating created_at/updated_at."""
    return datetime.now(timezone.utc)


def test_create_sets_is_active_default_true(app):
    """ShortURL.create() defaults is_active to True when not explicitly set."""
    url = ShortURL.create(
        short_code="abc123",
        original_url="https://example.com",
        created_at=_now(),
        updated_at=_now(),
    )

    assert url.is_active is True


def test_short_code_must_be_unique(app):
    """A duplicate short_code raises IntegrityError, confirming the unique constraint."""
    now = _now()
    ShortURL.create(
        short_code="dupe01",
        original_url="https://example.com/one",
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(IntegrityError):
        ShortURL.create(
            short_code="dupe01",
            original_url="https://example.com/two",
            created_at=now,
            updated_at=now,
        )


def test_user_id_and_title_are_optional(app):
    """user_id and title accept null values, confirming they're not required."""
    url = ShortURL.create(
        short_code="opt001",
        original_url="https://example.com",
        created_at=_now(),
        updated_at=_now(),
    )

    assert url.user_id is None
    assert url.title is None
