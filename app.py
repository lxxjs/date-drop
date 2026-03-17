import json
import os
import secrets
import smtplib
import sqlite3
import time
from email.message import EmailMessage
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "date_drop.db"


def load_local_env() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_local_env()

ALLOWED_DOMAINS = ("@stu.pku.edu.cn", "@mails.tsinghua.edu.cn")
CODE_TTL_SECONDS = int(os.getenv("CODE_TTL_SECONDS", "600"))
RESEND_COOLDOWN_SECONDS = int(os.getenv("RESEND_COOLDOWN_SECONDS", "45"))

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "date-drop-dev-secret")

verification_store = {}


def get_db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                answers_json TEXT NOT NULL,
                submitted_at INTEGER NOT NULL
            )
            """
        )
        connection.commit()


init_db()


def profile_exists(email: str) -> bool:
    if not email:
        return False

    normalized = normalize_email(email)
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM profiles WHERE email = ? LIMIT 1",
            (normalized,),
        ).fetchone()
    return row is not None


def normalize_email(value: str) -> str:
    return value.strip().lower()


def is_allowed_email(value: str) -> bool:
    email = normalize_email(value)
    return any(email.endswith(domain) for domain in ALLOWED_DOMAINS)


def smtp_is_configured() -> bool:
    return all([SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM])


def send_verification_email(email: str, code: str) -> None:
    if not smtp_is_configured():
        raise RuntimeError(
            "SMTP is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, "
            "SMTP_PASSWORD, SMTP_FROM, and APP_SECRET_KEY before sending codes."
        )

    message = EmailMessage()
    message["Subject"] = "Your Date Drop verification code"
    message["From"] = SMTP_FROM
    message["To"] = email
    message.set_content(
        "Use this Date Drop verification code to sign in:\n\n"
        f"{code}\n\n"
        f"This code expires in {CODE_TTL_SECONDS // 60} minutes."
    )

    if SMTP_USE_SSL:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
        return

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)


# ── Page routes ──────────────────────────────────────────────


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/questions")
def questions():
    email = normalize_email(request.args.get("email", "")) or session.get("verified_email", "")
    email = normalize_email(email)
    if email and profile_exists(email):
        session["verified_email"] = email
        return redirect("/home")

    return render_template("questions.html")


@app.get("/home")
def home():
    return render_template("home.html")


@app.get("/cupid")
def cupid():
    return render_template("cupid.html")


# ── API routes ───────────────────────────────────────────────


@app.post("/api/send-code")
def send_code():
    payload = request.get_json(silent=True) or {}
    email = normalize_email(payload.get("email", ""))

    if not email:
        return jsonify({"ok": False, "message": "Enter your school email first."}), 400

    if not is_allowed_email(email):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "Only @stu.pku.edu.cn or @mails.tsinghua.edu.cn emails are allowed.",
                }
            ),
            400,
        )

    existing = verification_store.get(email)
    now = int(time.time())
    if existing and now - existing["sent_at"] < RESEND_COOLDOWN_SECONDS:
        retry_after = RESEND_COOLDOWN_SECONDS - (now - existing["sent_at"])
        return (
            jsonify(
                {
                    "ok": False,
                    "message": f"Please wait {retry_after}s before requesting a new code.",
                }
            ),
            429,
        )

    code = f"{secrets.randbelow(1000000):06d}"
    verification_store[email] = {
        "code": code,
        "sent_at": now,
        "expires_at": now + CODE_TTL_SECONDS,
    }

    try:
        send_verification_email(email, code)
    except Exception as exc:
        verification_store.pop(email, None)
        return jsonify({"ok": False, "message": str(exc)}), 503

    return jsonify(
        {
            "ok": True,
            "message": f"Verification code sent to {email}.",
            "expires_in": CODE_TTL_SECONDS,
        }
    )


@app.post("/api/verify-code")
def verify_code():
    payload = request.get_json(silent=True) or {}
    email = normalize_email(payload.get("email", ""))
    code = str(payload.get("code", "")).strip()

    if not is_allowed_email(email):
        return jsonify({"ok": False, "message": "Use an approved campus email."}), 400

    if not code.isdigit() or len(code) != 6:
        return jsonify({"ok": False, "message": "Enter the 6-digit code."}), 400

    record = verification_store.get(email)
    if not record:
        return jsonify({"ok": False, "message": "Request a new verification code first."}), 400

    if int(time.time()) > record["expires_at"]:
        verification_store.pop(email, None)
        return jsonify({"ok": False, "message": "That code has expired. Request a new one."}), 400

    if not secrets.compare_digest(record["code"], code):
        return jsonify({"ok": False, "message": "Incorrect verification code."}), 400

    session["verified_email"] = email
    verification_store.pop(email, None)
    return jsonify({"ok": True, "message": "Email verified.", "email": email})


@app.get("/api/session")
def get_session_state():
    return jsonify({"ok": True, "email": session.get("verified_email")})


@app.get("/api/profile-status")
def get_profile_status():
    email = normalize_email(request.args.get("email", "")) or session.get("verified_email", "")
    email = normalize_email(email)
    exists = profile_exists(email) if email else False

    if email:
        session["verified_email"] = email

    return jsonify({"ok": True, "email": email or None, "has_profile": exists})


@app.post("/api/profile")
def save_profile():
    payload = request.get_json(silent=True) or {}
    answers = payload.get("answers")
    email = normalize_email(payload.get("email", "")) or session.get("verified_email", "")
    email = normalize_email(email)

    if not email:
        return jsonify({"ok": False, "message": "Missing email."}), 400

    if not is_allowed_email(email):
        return jsonify({"ok": False, "message": "Use an approved campus email."}), 400

    if not isinstance(answers, dict) or not answers:
        return jsonify({"ok": False, "message": "No questionnaire answers received."}), 400

    submitted_at = int(time.time())

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO profiles (email, answers_json, submitted_at)
            VALUES (?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                answers_json = excluded.answers_json,
                submitted_at = excluded.submitted_at
            """,
            (email, json.dumps(answers), submitted_at),
        )
        connection.commit()

    session["verified_email"] = email
    return jsonify({"ok": True, "email": email, "submitted_at": submitted_at})


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8765")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
