import logging

from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Config

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(Config)

    # Register blueprints
    from app.routes.pages import pages
    from app.routes.profiles import profiles
    from app.routes.matches import matches
    from app.routes.chat import chat
    from app.routes.cupid import cupid
    from app.routes.invites import invites

    app.register_blueprint(pages)
    app.register_blueprint(profiles)
    app.register_blueprint(matches)
    app.register_blueprint(chat)
    app.register_blueprint(cupid)
    app.register_blueprint(invites)

    # Auth session endpoint
    from app.routes.auth_session import auth_session
    app.register_blueprint(auth_session)

    # Centralized error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"ok": False, "message": str(e.description)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"ok": False, "message": "Authentication required."}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"ok": False, "message": "Forbidden."}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"ok": False, "message": "Not found."}), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Internal server error")
        return jsonify({"ok": False, "message": "Internal server error."}), 500

    # Trust Railway's reverse proxy headers (X-Forwarded-For, -Proto, -Host)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    return app
