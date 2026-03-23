import logging
import uuid

from flask import Blueprint, g, jsonify, request

from app.auth import require_auth
from app.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# The 6 quick-match dimensions (subset of the 16 full dimensions)
QUICK_MATCH_DIMENSIONS = [
    "s_social_energy", "s_ambition", "s_monogamy",
    "s_shared_values", "s_spontaneity", "s_humor",
]

profiles = Blueprint("profiles", __name__)


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _map_answers_to_row(answers: dict) -> dict:
    """Map flat form answers to structured profile columns."""

    def _int(val, default=None):
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    # Traits may arrive as a list or a single value
    def _to_list(val):
        if isinstance(val, list):
            return val
        if isinstance(val, str) and val:
            return [val]
        return []

    return {
        "full_name": answers.get("fullName", ""),
        "gender": answers.get("gender", ""),
        "major_one": answers.get("majorOne", ""),
        "major_two": answers.get("majorTwo") or None,
        "race": answers.get("race", ""),
        "preferred_race": answers.get("preferredRace") or None,
        "height_cm": _int(answers.get("height")),
        "preferred_height_min": _int(answers.get("preferredHeightMin"), 155),
        "preferred_height_max": _int(answers.get("preferredHeightMax"), 190),
        "relationship_goal": answers.get("relationshipGoal", ""),
        "birth_date": answers.get("birthDate", ""),
        "preferred_age_min": _int(answers.get("preferredAgeMin"), 18),
        "preferred_age_max": _int(answers.get("preferredAgeMax"), 26),
        "grad_year": _int(answers.get("gradYear")),
        "grad_preference": answers.get("gradPreference", ""),
        "religion": answers.get("religion") or None,
        "preferred_religion": answers.get("preferredReligion") or None,
        "date_ideas": answers.get("dateIdeas") or None,
        "self_traits": _to_list(answers.get("selfTraits")),
        "partner_traits": _to_list(answers.get("partnerTraits")),
        "s_children": _int(answers.get("children"), 4),
        "s_religion_imp": _int(answers.get("religion_imp"), 4),
        "s_career_fam": _int(answers.get("career_fam"), 4),
        "s_monogamy": _int(answers.get("monogamy"), 4),
        "s_shared_values": _int(answers.get("shared_values"), 4),
        "s_conflict_style": _int(answers.get("conflict_style"), 4),
        "s_social_energy": _int(answers.get("social_energy"), 4),
        "s_politics": _int(answers.get("politics"), 4),
        "s_ambition": _int(answers.get("ambition"), 4),
        "s_tidiness": _int(answers.get("tidiness"), 4),
        "s_spontaneity": _int(answers.get("spontaneity"), 4),
        "s_physical": _int(answers.get("physical"), 4),
        "s_comm_freq": _int(answers.get("comm_freq"), 4),
        "s_future_city": _int(answers.get("future_city"), 4),
        "s_pace": _int(answers.get("pace"), 4),
        "s_humor": _int(answers.get("humor"), 4),
        "phone_number": answers.get("phoneNumber") or None,
        "final_notes": answers.get("finalNotes") or None,
        "friends": answers.get("friends") or None,
    }


def _log_analytics(sb, user_id: str, event_type: str, metadata: dict) -> None:
    """Fire-and-forget analytics event logging."""
    try:
        sb.table("analytics_events").insert({
            "user_id": user_id,
            "event_type": event_type,
            "metadata_json": metadata,
        }).execute()
    except Exception:
        logger.exception("Failed to log analytics event %s for %s", event_type, user_id)


@profiles.get("/api/allowed-schools")
def get_allowed_schools():
    sb = get_supabase()
    result = sb.table("allowed_schools").select("domain, name, short_name").execute()
    return jsonify({"ok": True, "schools": result.data})


@profiles.get("/api/profile-status")
@require_auth
def get_profile_status():
    sb = get_supabase()
    email = g.user["email"]
    result = (
        sb.table("profiles")
        .select("id")
        .eq("user_id", g.user["id"])
        .maybe_single()
        .execute()
    )
    has_profile = result.data is not None
    return jsonify({"ok": True, "email": email, "has_profile": has_profile})


@profiles.post("/api/profile")
@require_auth
def save_profile():
    payload = request.get_json(silent=True) or {}
    answers = payload.get("answers")
    quick_match = payload.get("quick_match", False)

    if not isinstance(answers, dict) or not answers:
        return jsonify({"ok": False, "message": "No questionnaire answers received."}), 400

    sb = get_supabase()
    email = g.user["email"]
    user_id = g.user["id"]

    # Log questionnaire_started event (fire-and-forget)
    _log_analytics(sb, user_id, "questionnaire_started", {
        "mode": "quick" if quick_match else "full",
    })

    row = _map_answers_to_row(answers)
    row["user_id"] = user_id
    row["email"] = email
    row["is_quick_match"] = quick_match

    # Look up school_id from email domain
    for school in sb.table("allowed_schools").select("id, domain").execute().data:
        if email.endswith(school["domain"]):
            row["school_id"] = school["id"]
            break

    sb.table("profiles").upsert(row, on_conflict="user_id").execute()

    # Log questionnaire_completed event (fire-and-forget)
    completed_dimensions = [
        dim for dim in QUICK_MATCH_DIMENSIONS
        if row.get(dim) is not None
    ] if quick_match else [
        k for k in row if k.startswith("s_") and row[k] is not None
    ]
    _log_analytics(sb, user_id, "questionnaire_completed", {
        "mode": "quick" if quick_match else "full",
        "dimensions_completed": len(completed_dimensions),
        "last_dimension": completed_dimensions[-1] if completed_dimensions else None,
    })

    return jsonify({"ok": True, "email": email})


@profiles.post("/api/profile/photo")
@require_auth
def upload_photo():
    if "photo" not in request.files:
        return jsonify({"ok": False, "message": "No photo file provided."}), 400

    file = request.files["photo"]
    if not file.filename:
        return jsonify({"ok": False, "message": "Empty file."}), 400

    content_type = file.content_type or ""
    if content_type not in ("image/jpeg", "image/png"):
        return jsonify({"ok": False, "message": "Only JPEG and PNG images are allowed."}), 400

    file_bytes = file.read()
    max_size = 5 * 1024 * 1024  # 5MB
    if len(file_bytes) > max_size:
        return jsonify({"ok": False, "message": "Photo must be under 5 MB."}), 400

    ext = "jpg" if "jpeg" in content_type else "png"
    user_id = g.user["id"]
    file_name = f"{user_id}/{uuid.uuid4().hex}.{ext}"

    sb = get_supabase()
    sb.storage.from_("profile-photos").upload(
        file_name,
        file_bytes,
        {"content-type": content_type},
    )

    photo_url = f"{sb.supabase_url}/storage/v1/object/public/profile-photos/{file_name}"

    sb.table("profiles").update({"photo_url": photo_url}).eq("user_id", user_id).execute()

    return jsonify({"ok": True, "photo_url": photo_url})


@profiles.post("/api/profile/opt-in")
@require_auth
def opt_in():
    sb = get_supabase()
    sb.table("profiles").update({"is_opted_in": True}).eq("user_id", g.user["id"]).execute()
    return jsonify({"ok": True, "message": "You're opted in for this week's matching round."})
