from flask import Flask

from app.config import Config


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

    app.register_blueprint(pages)
    app.register_blueprint(profiles)
    app.register_blueprint(matches)
    app.register_blueprint(chat)
    app.register_blueprint(cupid)

    # Auth session endpoint
    from app.routes.auth_session import auth_session
    app.register_blueprint(auth_session)

    return app
