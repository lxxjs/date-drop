"""Fire-and-forget email notifications via Resend.

Failures are logged but never block the caller.
"""

import logging

import resend

from app.config import Config

logger = logging.getLogger(__name__)


def send_match_email(to_email: str, app_url: str | None = None) -> bool:
    """Send a match notification email. Returns True on success, False on failure."""
    if not Config.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — skipping email to %s", to_email)
        return False

    resend.api_key = Config.RESEND_API_KEY
    url = app_url or Config.APP_URL

    try:
        resend.Emails.send({
            "from": "Date Drop <notifications@datedrop.app>",
            "to": [to_email],
            "subject": "You have a new match on Date Drop!",
            "html": (
                "<p>You have a new match on Date Drop!</p>"
                f'<p><a href="{url}/home">Open the app to see who</a></p>'
            ),
        })
        logger.info("Match email sent to %s", to_email)
        return True
    except Exception:
        logger.exception("Failed to send match email to %s", to_email)
        return False
