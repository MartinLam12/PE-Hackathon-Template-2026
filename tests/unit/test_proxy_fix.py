"""Unit tests for ProxyFix when running behind Nginx."""

from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app


def test_proxy_fix_enabled_when_trust_headers_set(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "1")

    app = create_app()
    assert isinstance(app.wsgi_app, ProxyFix)


def test_proxy_fix_disabled_when_unset(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)

    app = create_app()
    assert not isinstance(app.wsgi_app, ProxyFix)


def test_proxy_fix_disabled_when_explicitly_off(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "0")

    app = create_app()
    assert not isinstance(app.wsgi_app, ProxyFix)
