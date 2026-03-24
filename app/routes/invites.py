"""Invite link routes for the viral growth loop.

Endpoints:
  POST /api/invite/create   — Create a new invite link (auth required, 5 max)
  GET  /api/invite/<code>   — Get invite metadata (for the landing page JS)
  POST /api/invite/redeem   — Mark an invite as used after signup
  GET  /api/invite/mine     — List the current user's invite links
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, g, jsonify, request

from app.auth import require_auth
from app.supabase_client import exec_single, get_supabase

logger = logging.getLogger(__name__)

invites = Blueprint("invites", __name__)

INVITE_QUOTA = 5
INVITE_EXPIRY_DAYS = 30


@invites.post("/api/invite/create")
@require_auth
def create_invite():
    sb = get_supabase()
    user_id = g.user["id"]

    # Look up the user's profile to get their profile id
    profile = exec_single(
        sb.table("profiles")
        .select("id, school_id")
        .eq("user_id", user_id)
    )
    if not profile.data:
        return jsonify({"ok": False, "message": "Complete your profile first."}), 400

    inviter_profile_id = profile.data["id"]

    # Quota enforcement
    existing = (
        sb.table("invites")
        .select("id", count="exact")
        .eq("inviter_id", inviter_profile_id)
        .execute()
    )
    if existing.count >= INVITE_QUOTA:
        return jsonify({
            "ok": False,
            "message": f"You've reached the maximum of {INVITE_QUOTA} invite links.",
        }), 400

    # Generate unique invite code
    invite_code = secrets.token_urlsafe(6)  # 8 base64url chars
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=INVITE_EXPIRY_DAYS)

    row = {
        "inviter_id": inviter_profile_id,
        "invite_code": invite_code,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }

    sb.table("invites").insert(row).execute()

    return jsonify({
        "ok": True,
        "invite_code": invite_code,
        "expires_at": expires_at.isoformat(),
    }), 201


@invites.get("/api/invite/<code>")
def get_invite(code):
    """Public endpoint — returns invite metadata for the landing page."""
    sb = get_supabase()

    invite = exec_single(
        sb.table("invites")
        .select("id, invite_code, used_by, expires_at, inviter_id")
        .eq("invite_code", code)
    )
    if not invite.data:
        return jsonify({"ok": False, "message": "Invalid invite link."}), 404

    # Check expiry
    expires_at = datetime.fromisoformat(invite.data["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        return jsonify({"ok": False, "message": "This invite has expired."}), 410

    # Check if already used
    if invite.data["used_by"] is not None:
        return jsonify({"ok": False, "message": "This invite has already been used."}), 410

    # Get school name for the landing page (via inviter's profile)
    school_name = "your university"
    inviter_profile = exec_single(
        sb.table("profiles")
        .select("school_id")
        .eq("id", invite.data["inviter_id"])
    )
    if inviter_profile.data and inviter_profile.data.get("school_id"):
        school = exec_single(
            sb.table("allowed_schools")
            .select("name")
            .eq("id", inviter_profile.data["school_id"])
        )
        if school.data:
            school_name = school.data["name"]

    # Social proof counter — threshold-based
    total_profiles = (
        sb.table("profiles")
        .select("id", count="exact")
        .execute()
    )
    count = total_profiles.count or 0

    if count >= 100:
        social_proof = "100+ students have already joined"
    elif count >= 50:
        social_proof = "50+ students have already joined"
    elif count >= 10:
        social_proof = f"{(count // 10) * 10}+ students have already joined"
    else:
        social_proof = f"Be one of the first at {school_name}"

    return jsonify({
        "ok": True,
        "invite_code": code,
        "school_name": school_name,
        "social_proof": social_proof,
    })


@invites.post("/api/invite/redeem")
@require_auth
def redeem_invite():
    """Called after signup to mark the invite as used and link inviter."""
    payload = request.get_json(silent=True) or {}
    invite_code = payload.get("invite_code", "").strip()

    if not invite_code:
        return jsonify({"ok": False, "message": "invite_code is required."}), 400

    sb = get_supabase()
    user_id = g.user["id"]

    # Get the new user's profile
    profile = exec_single(
        sb.table("profiles")
        .select("id")
        .eq("user_id", user_id)
    )
    if not profile.data:
        return jsonify({"ok": False, "message": "Complete your profile first."}), 400

    redeemer_profile_id = profile.data["id"]

    # Fetch the invite
    invite = exec_single(
        sb.table("invites")
        .select("id, inviter_id, used_by, expires_at")
        .eq("invite_code", invite_code)
    )
    if not invite.data:
        return jsonify({"ok": False, "message": "Invalid invite code."}), 404

    # Self-invite check
    if invite.data["inviter_id"] == redeemer_profile_id:
        return jsonify({"ok": False, "message": "You can't use your own invite."}), 400

    # Already used check
    if invite.data["used_by"] is not None:
        return jsonify({"ok": False, "message": "This invite has already been used."}), 410

    # Expiry check
    expires_at = datetime.fromisoformat(invite.data["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        return jsonify({"ok": False, "message": "This invite has expired."}), 410

    # Mark as used
    sb.table("invites").update({
        "used_by": redeemer_profile_id,
    }).eq("id", invite.data["id"]).execute()

    # Get inviter's name to reveal on the home page
    inviter = exec_single(
        sb.table("profiles")
        .select("full_name")
        .eq("id", invite.data["inviter_id"])
    )
    inviter_name = inviter.data["full_name"] if inviter.data else "Someone"

    return jsonify({
        "ok": True,
        "inviter_name": inviter_name,
        "message": f"{inviter_name} invited you to Date Drop!",
    })


@invites.get("/api/invite/mine")
@require_auth
def my_invites():
    """List the current user's invite links."""
    sb = get_supabase()
    user_id = g.user["id"]

    profile = exec_single(
        sb.table("profiles")
        .select("id")
        .eq("user_id", user_id)
    )
    if not profile.data:
        return jsonify({"ok": True, "invites": []})

    result = (
        sb.table("invites")
        .select("invite_code, used_by, created_at, expires_at")
        .eq("inviter_id", profile.data["id"])
        .order("created_at", desc=True)
        .execute()
    )

    invite_list = []
    now = datetime.now(timezone.utc)
    for inv in result.data:
        expires_at = datetime.fromisoformat(inv["expires_at"])
        status = "used" if inv["used_by"] else ("expired" if now > expires_at else "active")
        invite_list.append({
            "invite_code": inv["invite_code"],
            "status": status,
            "created_at": inv["created_at"],
            "expires_at": inv["expires_at"],
        })

    return jsonify({
        "ok": True,
        "invites": invite_list,
        "remaining": INVITE_QUOTA - len(invite_list),
    })
