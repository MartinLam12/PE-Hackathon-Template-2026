import os

from flask import request
from peewee import DatabaseProxy, Model, OperationalError
from playhouse.pool import PooledPostgresqlDatabase
from werkzeug.exceptions import ServiceUnavailable

db = DatabaseProxy()

# Endpoints that must answer even when Postgres is unreachable. /health is
# probed by the load balancer, so making it depend on the database would pull
# otherwise-healthy instances out of rotation during a database incident.
NO_DB_ENDPOINTS = {"health"}


class BaseModel(Model):
    class Meta:
        database = db


def init_db(app):
    # PooledPostgresqlDatabase keeps connections open and hands them back out
    # instead of doing a TCP connect + auth handshake on every request.
    # See docs/performance.md — per-request connection setup was a measurable
    # cost once concurrency went up.
    #
    # max_connections is per worker *process*. Keep
    #   instances x gunicorn workers x max_connections
    # below Postgres' own max_connections (default 100).
    database = PooledPostgresqlDatabase(
        os.environ.get("DATABASE_NAME", "hackathon_db"),
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=int(os.environ.get("DATABASE_PORT", 5432)),
        user=os.environ.get("DATABASE_USER", "postgres"),
        password=os.environ.get("DATABASE_PASSWORD", "postgres"),
        max_connections=int(os.environ.get("DB_MAX_CONNECTIONS", 8)),
        # Recycle a connection after this long so a pooled handle never
        # outlives a server-side timeout or a restarted database.
        stale_timeout=int(os.environ.get("DB_STALE_TIMEOUT", 300)),
    )
    db.initialize(database)

    @app.before_request
    def _db_connect():
        if request.endpoint in NO_DB_ENDPOINTS:
            return

        try:
            db.connect(reuse_if_open=True)
        except OperationalError as exc:
            raise ServiceUnavailable(description="Database unavailable") from exc

    @app.teardown_appcontext
    def _db_close(exc):
        # For a pooled database, close() returns the connection to the pool
        # rather than tearing down the socket.
        if not db.is_closed():
            db.close()
