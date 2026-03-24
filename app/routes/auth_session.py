from flask import Blueprint, jsonify, make_response, request

import jwt

from app.auth import decode_supabase_jwt
from app.config import Config

auth_session = Blueprint("auth_session", __name__)


@auth_session.post("/api/auth/session")
def set_session():
    """Receive a Supabase access token from the frontend after successful OTP
    verification and set it as a secure httpOnly cookie for server-side auth."""
    payload = request.get_json(silent=True) or {}
    access_token = payload.get("access_token", "")
    refresh_token = payload.get("refresh_token", "")

    if not access_token:
        return jsonify({"ok": False, "message": "access_token is required."}), 400

    # Verify the token is valid
    try:
        decoded = decode_supabase_jwt(access_token)
    except jwt.InvalidTokenError:
        return jsonify({"ok": False, "message": "Invalid token."}), 401

    email = decoded.get("email", "")

    resp = make_response(jsonify({
        "ok": True,
        "email": email,
    }))

    # Set access token as httpOnly cookie
    is_prod = Config.SESSION_COOKIE_SECURE
    resp.set_cookie(
        "sb_access_token",
        access_token,
        httponly=True,
        secure=is_prod,
        samesite="Lax",
        max_age=3600,  # 1 hour (matches Supabase default token expiry)
        path="/",
    )

    if refresh_token:
        resp.set_cookie(
            "sb_refresh_token",
            refresh_token,
            httponly=True,
            secure=is_prod,
            samesite="Lax",
            max_age=60 * 60 * 24 * 30,  # 30 days
            path="/",
        )

    return resp


@auth_session.post("/api/auth/logout")
def logout():
    resp = make_response(jsonify({"ok": True}))
    resp.delete_cookie("sb_access_token", path="/")
    resp.delete_cookie("sb_refresh_token", path="/")
    return resp
