from functools import wraps

import jwt
from jwt import PyJWKClient
from flask import g, jsonify, request

from app.config import Config

# Cache the JWKS client — it fetches and caches public keys from Supabase
_jwks_client = None


def _get_jwks_client():
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{Config.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


def decode_supabase_jwt(token: str) -> dict:
    """Decode and verify a Supabase JWT using the project's JWKS public keys.

    Falls back to HS256 with the JWT secret if JWKS verification fails
    (supports both old HS256 and new ES256 Supabase projects).
    """
    # Try JWKS (ES256) first
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except Exception:
        pass

    # Fallback to HS256 (older Supabase projects)
    return jwt.decode(
        token,
        Config.SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience="authenticated",
    )


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
            payload = decode_supabase_jwt(token)
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
