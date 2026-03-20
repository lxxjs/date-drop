from functools import wraps

import jwt
from flask import g, jsonify, request

from app.config import Config


def require_auth(f):
    """Decorator that verifies the Supabase JWT from the auth cookie or
    Authorization header and attaches user info to ``g.user``."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Try cookie first, then Authorization header
        token = request.cookies.get("sb_access_token")
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if not token:
            return jsonify({"ok": False, "message": "Authentication required."}), 401

        try:
            payload = jwt.decode(
                token,
                Config.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"ok": False, "message": "Session expired. Please sign in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"ok": False, "message": "Invalid session."}), 401

        g.user = {
            "id": payload.get("sub"),
            "email": payload.get("email", ""),
        }
        return f(*args, **kwargs)

    return decorated
