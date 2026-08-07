def register_routes(app):
    """Attach all HTTP blueprints to the Flask app."""
    from app.routes.urls import urls_bp

    app.register_blueprint(urls_bp)
