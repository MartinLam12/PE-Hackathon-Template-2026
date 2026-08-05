import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from peewee import InterfaceError, OperationalError
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound, ServiceUnavailable
from werkzeug.middleware.proxy_fix import ProxyFix

from app.cache import init_cache
from app.database import db, init_db
from app.routes import register_routes


def create_app():
    load_dotenv()

    app = Flask(__name__)

    # Behind Nginx, the client's address and scheme arrive as X-Forwarded-*
    # headers; without this the app sees Nginx's IP as remote_addr. Off by
    # default because anything that can reach the app directly could
    # otherwise forge those headers — docker-compose.yml turns it on, where
    # Nginx is the only thing in front.
    if os.environ.get("TRUST_PROXY_HEADERS", "").lower() in {"1", "true", "yes"}:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    init_db(app)
    init_cache(app)

    from app import models  # noqa: F401 - registers models with Peewee

    register_routes(app)

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    @app.errorhandler(BadRequest)
    def handle_bad_request(error):
        return jsonify(error="bad_request", message=error.description), 400

    @app.errorhandler(NotFound)
    def handle_not_found(error):
        return jsonify(error="not_found", message=error.description), 404

    @app.errorhandler(ServiceUnavailable)
    def handle_service_unavailable(error):
        return jsonify(error="service_unavailable", message=error.description), 503

    @app.errorhandler(OperationalError)
    @app.errorhandler(InterfaceError)
    def handle_operational_error(error):
        # The connection we were handed may be dead rather than the database
        # being down — that is what happens after Postgres restarts under a
        # live pool. Evict the idle pooled connections so the next request
        # dials a fresh one instead of drawing another corpse. close_idle()
        # (not close_all()) because connections in use belong to other
        # in-flight requests.
        try:
            db.close_idle()
        except (OperationalError, InterfaceError, AttributeError):
            pass

        return jsonify(error="service_unavailable", message="Database unavailable"), 503

    @app.errorhandler(InternalServerError)
    def handle_internal_server_error(error):
        return jsonify(error="internal_server_error", message="Internal server error"), 500

    return app
