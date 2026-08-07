import secrets
import string
from datetime import datetime, timezone

from flask import Blueprint, abort, jsonify, redirect, request
from peewee import IntegrityError

from app.cache import cache
from app.models.url import ShortURL

urls_bp = Blueprint("urls", __name__)
ALPHABET = string.ascii_letters + string.digits

# GET /urls used to return every row in the table (see docs/performance.md).
# It is now paginated: DEFAULT_LIMIT keeps the common case small, MAX_LIMIT
# stops a client from asking for the unbounded response back.
DEFAULT_LIMIT = 50
MAX_LIMIT = 200

REDIRECT_TTL = 300  # short codes are immutable once created
DETAIL_TTL = 60


def _url_data(url):
    """Serialize a ShortURL row for JSON responses."""
    return {
        "id": url.id,
        "user_id": url.user_id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "title": url.title,
        "is_active": url.is_active,
        "created_at": url.created_at.isoformat() if url.created_at else None,
        "updated_at": url.updated_at.isoformat() if url.updated_at else None,
    }


def _new_code():
    """Generate a random six-character short code."""
    return "".join(secrets.choice(ALPHABET) for _ in range(6))


def _int_arg(name, default):
    """Parse an integer query arg, rejecting junk with a 400.

    `request.args.get(type=int)` silently returns the *default* when the
    value will not coerce, so `?limit=abc` would quietly behave as if no
    limit had been passed. Parse it directly instead.
    """
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        abort(400, description=f"{name} must be an integer")


@urls_bp.get("/urls")
def list_urls():
    """List URLs, newest-id last. Not cached: creates would make it stale."""
    limit = _int_arg("limit", DEFAULT_LIMIT)
    offset = _int_arg("offset", 0)
    if limit < 1:
        abort(400, description="limit must be at least 1")
    if offset < 0:
        abort(400, description="offset must not be negative")
    limit = min(limit, MAX_LIMIT)

    query = ShortURL.select().order_by(ShortURL.id)
    user_id = _int_arg("user_id", None)
    if user_id is not None:
        query = query.where(ShortURL.user_id == user_id)

    return jsonify([_url_data(url) for url in query.limit(limit).offset(offset)])


@urls_bp.post("/urls")
def create_url():
    """Create a new short URL from JSON input."""
    data = request.get_json(silent=True)
    if not data or not data.get("original_url"):
        abort(400, description="original_url is required")

    now = datetime.now(timezone.utc)
    for _ in range(5):
        try:
            url = ShortURL.create(
                user_id=data.get("user_id"),
                short_code=_new_code(),
                original_url=data["original_url"],
                title=data.get("title"),
                is_active=data.get("is_active", True),
                created_at=now,
                updated_at=now,
            )
            return jsonify(_url_data(url)), 201
        except IntegrityError:
            continue

    abort(503, description="Could not create a unique short URL")


@urls_bp.get("/urls/<short_code>")
@cache.cached(timeout=DETAIL_TTL)
def get_url(short_code):
    """Return JSON metadata for a short code."""
    url = ShortURL.get_or_none(ShortURL.short_code == short_code)
    if url is None:
        # abort() raises, so nothing is cached and a code created later is
        # picked up on the next request rather than serving a stale 404.
        abort(404, description="Short URL not found")
    return jsonify(_url_data(url))


@urls_bp.get("/<short_code>")
@cache.cached(timeout=REDIRECT_TTL)
def redirect_url(short_code):
    """The hot path: every click on a short link lands here.

    Caching it removes a database round trip per redirect, which is why
    this is the one route where caching genuinely earns its keep.
    """
    url = ShortURL.get_or_none(
        (ShortURL.short_code == short_code) & ShortURL.is_active
    )
    if url is None:
        abort(404, description="Short URL not found")
    return redirect(url.original_url)
