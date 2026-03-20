"""Legacy entry point -- use wsgi.py or `python -m flask run` instead.

Kept for backwards compatibility during local development.
"""

from app import create_app
from app.config import Config

application = create_app()

if __name__ == "__main__":
    application.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=True,
    )
