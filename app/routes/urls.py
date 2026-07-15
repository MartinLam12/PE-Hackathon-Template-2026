import secrets
import string
from datetime import datetime, timezone

from flask import Blueprint, abort, jsonify, redirect, request
from peewee import IntegrityError

from app.models.url import ShortURL

urls_bp = Blueprint("urls", __name__)
ALPHABET = string.ascii_letters + string.digits


def _url_data(url):
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
    return "".join(secrets.choice(ALPHABET) for _ in range(6))


@urls_bp.get("/urls")
def list_urls():
    query = ShortURL.select().order_by(ShortURL.id)
    user_id = request.args.get("user_id", type=int)
    if user_id is not None:
        query = query.where(ShortURL.user_id == user_id)
    return jsonify([_url_data(url) for url in query])


@urls_bp.post("/urls")
def create_url():
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
def get_url(short_code):
    url = ShortURL.get_or_none(ShortURL.short_code == short_code)
    if url is None:
        abort(404, description="Short URL not found")
    return jsonify(_url_data(url))


@urls_bp.get("/<short_code>")
def redirect_url(short_code):
    url = ShortURL.get_or_none(
        (ShortURL.short_code == short_code) & ShortURL.is_active
    )
    if url is None:
        abort(404, description="Short URL not found")
    return redirect(url.original_url)
