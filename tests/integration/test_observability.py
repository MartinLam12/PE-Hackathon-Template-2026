"""Integration tests for structured logging and /metrics (Incident Response Bronze)."""

from unittest.mock import patch

from peewee import OperationalError

from app.database import db


def test_metrics_endpoint_returns_prometheus_text(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.content_type
    body = response.get_data(as_text=True)
    assert "shortener_app_requests_total" in body or "flask_http_request" in body


def test_metrics_works_when_database_is_down(client):
    with patch.object(db.obj, "connect", side_effect=OperationalError("down")):
        response = client.get("/metrics")
    assert response.status_code == 200


def test_requests_are_structured_logged(client, app):
    with patch.object(app.logger, "info") as log_info:
        response = client.get("/health")
    assert response.status_code == 200
    logged_paths = [
        call.args[2]
        for call in log_info.call_args_list
        if call.args and call.args[0].startswith("request method=")
    ]
    assert "/health" in logged_paths
