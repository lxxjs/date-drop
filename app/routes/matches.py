from flask import Blueprint, g, jsonify, request

from app.auth import require_auth
from app.config import Config
from app.supabase_client import get_supabase

matches = Blueprint("matches", __name__)


@matches.get("/api/matches")
@require_auth
def get_matches():
    sb = get_supabase()

    # Get this user's profile id
    profile = (
        sb.table("profiles")
        .select("id")
        .eq("user_id", g.user["id"])
        .maybe_single()
        .execute()
    )
    if not profile.data:
        return jsonify({"ok": True, "matches": []})

    profile_id = profile.data["id"]

    # Fetch matches where this user is either user_a or user_b
    result_a = (
        sb.table("matches")
        .select("id, user_b_id, compatibility_score, match_reasons, match_round, status, created_at")
        .eq("user_a_id", profile_id)
        .order("created_at", desc=True)
        .execute()
    )
    result_b = (
        sb.table("matches")
        .select("id, user_a_id, compatibility_score, match_reasons, match_round, status, created_at")
        .eq("user_b_id", profile_id)
        .order("created_at", desc=True)
        .execute()
    )

    # Collect partner profile IDs
    match_list = []
    for m in result_a.data:
        match_list.append({**m, "partner_profile_id": m.pop("user_b_id")})
    for m in result_b.data:
        match_list.append({**m, "partner_profile_id": m.pop("user_a_id")})

    if not match_list:
        return jsonify({"ok": True, "matches": []})

    # Fetch partner profiles
    partner_ids = [m["partner_profile_id"] for m in match_list]
    partners = (
        sb.table("profiles")
        .select("id, full_name, major_one, photo_url, date_ideas")
        .in_("id", partner_ids)
        .execute()
    )
    partner_map = {p["id"]: p for p in partners.data}

    # Enrich matches with partner info
    enriched = []
    for m in match_list:
        partner = partner_map.get(m["partner_profile_id"], {})
        enriched.append({
            "id": m["id"],
            "compatibility_score": m["compatibility_score"],
            "match_reasons": m["match_reasons"],
            "match_round": m["match_round"],
            "status": m["status"],
            "created_at": m["created_at"],
            "partner": {
                "name": partner.get("full_name", ""),
                "major": partner.get("major_one", ""),
                "photo_url": partner.get("photo_url"),
                "date_ideas": partner.get("date_ideas"),
            },
        })

    # Sort by most recent
    enriched.sort(key=lambda x: x["created_at"], reverse=True)

    return jsonify({"ok": True, "matches": enriched})


@matches.post("/api/matches/<match_id>/respond")
@require_auth
def respond_to_match(match_id):
    payload = request.get_json(silent=True) or {}
    action = payload.get("action")
    if action not in ("accepted", "declined"):
        return jsonify({"ok": False, "message": "Action must be 'accepted' or 'declined'."}), 400

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

    # Verify this user is part of the match
    match = (
        sb.table("matches")
        .select("id, user_a_id, user_b_id")
        .eq("id", match_id)
        .maybe_single()
        .execute()
    )
    if not match.data:
        return jsonify({"ok": False, "message": "Match not found."}), 404

    if profile_id not in (match.data["user_a_id"], match.data["user_b_id"]):
        return jsonify({"ok": False, "message": "Not your match."}), 403

    sb.table("matches").update({"status": action}).eq("id", match_id).execute()
    return jsonify({"ok": True, "status": action})


@matches.post("/api/admin/generate-matches")
def generate_matches_admin():
    admin_key = request.headers.get("X-Admin-Key", "")
    if not Config.ADMIN_SECRET or admin_key != Config.ADMIN_SECRET:
        return jsonify({"ok": False, "message": "Unauthorized."}), 403

    payload = request.get_json(silent=True) or {}
    match_round = payload.get("match_round", "")
    if not match_round:
        return jsonify({"ok": False, "message": "match_round is required."}), 400

    from app.matching import generate_weekly_matches

    results = generate_weekly_matches(match_round)
    return jsonify({"ok": True, "matches_created": len(results)})
