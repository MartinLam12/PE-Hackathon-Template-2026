"""Structured logging and Prometheus metrics (Incident Response — Bronze)."""

import logging
import sys
import time

from flask import g, request
from prometheus_client import Counter
from prometheus_flask_exporter import PrometheusMetrics

APP_REQUESTS = Counter(
    "shortener_app_requests_total",
    "HTTP requests handled by the shortener",
    ["method", "endpoint", "status"],
)
APP_ERRORS = Counter(
    "shortener_app_errors_total",
    "HTTP 4xx/5xx responses",
    ["status"],
)


def _sanitize_log_value(value: str) -> str:
    """Strip control characters that could forge log records."""
    return value.replace("\r", "").replace("\n", "")


def configure_logging(app):
    """Structured logs: timestamp, level, logger name, message."""
    log_level = logging.DEBUG if app.debug else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    app.logger.propagate = False

    for logger_name in ("werkzeug", "gunicorn.error", "gunicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(log_level)
        logger.propagate = False


def init_observability(app):
    """Wire logging, request tracing, and metrics into the Flask app."""
    configure_logging(app)
    PrometheusMetrics(app, path="/metrics", group_by="endpoint")

    @app.before_request
    def _observability_start_timer():
        g._request_started_at = time.perf_counter()

    @app.after_request
    def _observability_log_and_count(response):
        duration_ms = (
            time.perf_counter() - g.get("_request_started_at", time.perf_counter())
        ) * 1000
        endpoint = request.endpoint or "unknown"
        status = response.status_code

        APP_REQUESTS.labels(request.method, endpoint, str(status)).inc()
        if status >= 400:
            APP_ERRORS.labels(str(status)).inc()

        app.logger.info(
            "request method=%s path=%s endpoint=%s status=%s duration_ms=%.2f",
            request.method,
            _sanitize_log_value(request.path),
            endpoint,
            status,
            duration_ms,
        )
        return response
