from flask import Blueprint, redirect, render_template, request

from app.config import Config

pages = Blueprint("pages", __name__)


@pages.get("/")
def index():
    return render_template(
        "index.html",
        supabase_url=Config.SUPABASE_URL,
        supabase_anon_key=Config.SUPABASE_ANON_KEY,
    )


@pages.get("/questions")
def questions():
    return render_template(
        "questions.html",
        supabase_url=Config.SUPABASE_URL,
        supabase_anon_key=Config.SUPABASE_ANON_KEY,
    )


@pages.get("/home")
def home():
    return render_template(
        "home.html",
        supabase_url=Config.SUPABASE_URL,
        supabase_anon_key=Config.SUPABASE_ANON_KEY,
    )


@pages.get("/cupid")
def cupid():
    return render_template(
        "cupid.html",
        supabase_url=Config.SUPABASE_URL,
        supabase_anon_key=Config.SUPABASE_ANON_KEY,
    )


@pages.get("/chat/<match_id>")
def chat(match_id):
    return render_template(
        "chat.html",
        match_id=match_id,
        supabase_url=Config.SUPABASE_URL,
        supabase_anon_key=Config.SUPABASE_ANON_KEY,
    )


@pages.get("/invite/<code>")
def invite_landing(code):
    return render_template(
        "invite.html",
        invite_code=code,
        supabase_url=Config.SUPABASE_URL,
        supabase_anon_key=Config.SUPABASE_ANON_KEY,
    )
