from flask import Blueprint, g, jsonify, request

from app.auth import require_auth
from app.supabase_client import get_supabase

chat = Blueprint("chat", __name__)


def _user_is_in_match(sb, profile_id: str, match_id: str) -> bool:
    match = (
        sb.table("matches")
        .select("user_a_id, user_b_id")
        .eq("id", match_id)
        .maybe_single()
        .execute()
    )
    if not match.data:
        return False
    return profile_id in (match.data["user_a_id"], match.data["user_b_id"])


@chat.get("/api/messages/<match_id>")
@require_auth
def get_messages(match_id):
    sb = get_supabase()

    profile = (
        sb.table("profiles")
        .select("id")
        .eq("user_id", g.user["id"])
        .maybe_single()
        .execute()
    )
    if not profile.data:
        return jsonify({"ok": False, "message": "Profile not found."}), 404

    if not _user_is_in_match(sb, profile.data["id"], match_id):
        return jsonify({"ok": False, "message": "Not your match."}), 403

    page = request.args.get("page", 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    result = (
        sb.table("messages")
        .select("id, sender_id, content, created_at")
        .eq("match_id", match_id)
        .order("created_at", desc=False)
        .range(offset, offset + per_page - 1)
        .execute()
    )

    return jsonify({
        "ok": True,
        "messages": result.data,
        "my_profile_id": profile.data["id"],
    })


@chat.post("/api/messages")
@require_auth
def send_message():
    payload = request.get_json(silent=True) or {}
    match_id = payload.get("match_id", "")
    content = (payload.get("content") or "").strip()

    if not match_id:
        return jsonify({"ok": False, "message": "match_id is required."}), 400
    if not content:
        return jsonify({"ok": False, "message": "Message content is required."}), 400
    if len(content) > 2000:
        return jsonify({"ok": False, "message": "Message too long (max 2000 chars)."}), 400

    sb = get_supabase()

    profile = (
        sb.table("profiles")
        .select("id")
        .eq("user_id", g.user["id"])
        .maybe_single()
        .execute()
    )
    if not profile.data:
        return jsonify({"ok": False, "message": "Profile not found."}), 404

    profile_id = profile.data["id"]
    if not _user_is_in_match(sb, profile_id, match_id):
        return jsonify({"ok": False, "message": "Not your match."}), 403

    result = (
        sb.table("messages")
        .insert({
            "match_id": match_id,
            "sender_id": profile_id,
            "content": content,
        })
        .execute()
    )

    return jsonify({"ok": True, "message": result.data[0] if result.data else {}})
