from dotenv import load_dotenv
from flask import Flask, jsonify
from peewee import OperationalError
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound, ServiceUnavailable

from app.database import init_db
from app.routes import register_routes


def create_app():
    load_dotenv()

    app = Flask(__name__)

    init_db(app)

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
    def handle_database_error(error):
        return jsonify(error="service_unavailable", message="Database unavailable"), 503

    @app.errorhandler(InternalServerError)
    def handle_internal_server_error(error):
        return jsonify(error="internal_server_error", message="Internal server error"), 500

    return app
