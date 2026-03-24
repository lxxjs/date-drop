# Date Drop

A campus dating app for Chinese universities. Users verify via school email (Supabase OTP), fill out a questionnaire, get matched weekly, and can chat with matches. Includes a "Cupid" feature for friend-pair nominations and a viral invite system.

## Tech Stack

- Python 3 / Flask
- Supabase (PostgreSQL + Auth + Storage)
- HTML/CSS/Vanilla JavaScript (Jinja2 templates)
- Resend (email notifications)
- Railway (deployment)

## Local Setup

```bash
cd date-drop
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in Supabase credentials
python app.py
```

Open: [http://localhost:8765](http://localhost:8765)

## Environment Variables

See `.env.example`. Required: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`. Optional: `ADMIN_SECRET`, `RESEND_API_KEY`, `APP_URL`, `PORT`.

## Routes

### Pages

| Route | Description |
|-------|-------------|
| `GET /` | Landing page |
| `GET /questions` | Profile questionnaire (full or quick match mode) |
| `GET /home` | Matches home page |
| `GET /cupid` | Cupid nominations page |
| `GET /chat/<match_id>` | Chat with a match |
| `GET /invite/<code>` | Campus invite landing page |

### APIs

| Route | Description |
|-------|-------------|
| `POST /api/auth/session` | Set auth cookies from Supabase token |
| `POST /api/auth/logout` | Clear auth cookies |
| `GET /api/profile-status` | Check if user has a profile |
| `POST /api/profile` | Save questionnaire answers |
| `POST /api/profile/photo` | Upload profile photo |
| `POST /api/profile/opt-in` | Opt in for weekly matching |
| `GET /api/allowed-schools` | List whitelisted university domains |
| `GET /api/matches` | List user's matches |
| `POST /api/matches/<id>/respond` | Accept/decline a match |
| `GET /api/messages/<match_id>` | Get chat messages |
| `POST /api/messages` | Send a chat message |
| `POST /api/cupid/nominate` | Submit a cupid nomination |
| `GET /api/cupid/leaderboard` | Cupid points leaderboard |
| `POST /api/invite/create` | Create an invite link (5 max) |
| `GET /api/invite/<code>` | Get invite metadata |
| `POST /api/invite/redeem` | Redeem an invite after signup |
| `GET /api/invite/mine` | List user's invite links |
| `POST /api/admin/generate-matches` | Trigger weekly matching (admin) |
| `GET /api/admin/stats` | Dashboard stats (admin) |

## Testing

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

29 tests covering invite CRUD, email notifications, admin stats, and page rendering.

## Deployment

Railway via nixpacks. Config in `railway.toml`. Production command: `gunicorn wsgi:app`.
