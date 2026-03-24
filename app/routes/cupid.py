from flask import Blueprint, g, jsonify, request

from app.auth import require_auth
from app.supabase_client import exec_single, get_supabase

cupid = Blueprint("cupid", __name__)

MAX_NOMINATIONS_PER_ROUND = 4


@cupid.post("/api/cupid/nominate")
@require_auth
def nominate():
    payload = request.get_json(silent=True) or {}
    nominee_a = (payload.get("nominee_a_email") or "").strip().lower()
    nominee_b = (payload.get("nominee_b_email") or "").strip().lower()
    match_round = (payload.get("match_round") or "").strip()

    if not nominee_a or not nominee_b:
        return jsonify({"ok": False, "message": "Two email addresses are required."}), 400
    if nominee_a == nominee_b:
        return jsonify({"ok": False, "message": "Please enter two different people."}), 400
    if not match_round:
        return jsonify({"ok": False, "message": "match_round is required."}), 400

    sb = get_supabase()

    profile = exec_single(
        sb.table("profiles")
        .select("id")
        .eq("user_id", g.user["id"])
    )
    if not profile.data:
        return jsonify({"ok": False, "message": "Complete your profile first."}), 400

    nominator_id = profile.data["id"]

    # Check nomination count for this round
    existing = (
        sb.table("cupid_nominations")
        .select("id", count="exact")
        .eq("nominator_id", nominator_id)
        .eq("match_round", match_round)
        .execute()
    )
    if existing.count is not None and existing.count >= MAX_NOMINATIONS_PER_ROUND:
        return jsonify({"ok": False, "message": f"You've used all {MAX_NOMINATIONS_PER_ROUND} nominations this round."}), 400

    sb.table("cupid_nominations").insert({
        "nominator_id": nominator_id,
        "nominee_a_email": nominee_a,
        "nominee_b_email": nominee_b,
        "match_round": match_round,
    }).execute()

    remaining = MAX_NOMINATIONS_PER_ROUND - (existing.count or 0) - 1
    return jsonify({"ok": True, "remaining": remaining})


@cupid.get("/api/cupid/leaderboard")
def leaderboard():
    sb = get_supabase()

    # Get all nominations with points > 0, grouped by nominator
    result = (
        sb.table("cupid_nominations")
        .select("nominator_id, points_awarded")
        .gt("points_awarded", 0)
        .execute()
    )

    # Aggregate points by nominator
    scores: dict[str, int] = {}
    for row in result.data:
        nid = row["nominator_id"]
        scores[nid] = scores.get(nid, 0) + row["points_awarded"]

    if not scores:
        return jsonify({"ok": True, "leaderboard": []})

    # Fetch nominator names for display (initials only for privacy)
    nominator_ids = list(scores.keys())
    profiles_result = (
        sb.table("profiles")
        .select("id, full_name")
        .in_("id", nominator_ids)
        .execute()
    )
    name_map = {p["id"]: p["full_name"] for p in profiles_result.data}

    leaderboard_data = []
    for nid, total in scores.items():
        full_name = name_map.get(nid, "")
        parts = full_name.split()
        initials = ".".join(p[0].upper() for p in parts if p) + "." if parts else "?"
        leaderboard_data.append({"initials": initials, "points": total})

    leaderboard_data.sort(key=lambda x: x["points"], reverse=True)

    return jsonify({"ok": True, "leaderboard": leaderboard_data})
