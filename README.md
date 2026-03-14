# Date Drop

A lightweight Flask web app for a campus dating flow:

- Landing page with campus email entry
- Multi-step profile questionnaire
- Profile saved to SQLite
- Home (Matches) page
- Cupid page UI with mock shipping interaction

## Tech Stack

- Python 3
- Flask
- SQLite (via Python `sqlite3`)
- HTML/CSS/Vanilla JavaScript

## Project Structure

- `app.py` - Flask app and API/routes
- `index.html`, `style.css`, `script.js` - landing page
- `questions.html`, `questions.css`, `questions.js` - onboarding questionnaire
- `home.html`, `home.css` - matches home page
- `cupid.html`, `cupid.css`, `cupid.js` - cupid page
- `requirements.txt` - Python dependencies

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: [http://localhost:8765](http://localhost:8765)

If you want another port:

```bash
PORT=5000 python app.py
```

## Current Routes

### Pages

- `GET /` - landing page
- `GET /questions` - questionnaire
- `GET /home` - matches home page
- `GET /cupid` - cupid page

### APIs

- `POST /api/send-code`
- `POST /api/verify-code`
- `GET /api/session`
- `GET /api/profile-status`
- `POST /api/profile`

## Database

The app creates `date_drop.db` automatically in the project root.

`profiles` table stores:

- `email` (unique)
- `answers_json` (questionnaire payload)
- `submitted_at` (unix timestamp)

## Returning User Behavior

- If a user already has a saved profile, they are redirected to `/home`.
- New users continue to `/questions`.

## Notes

- This is a development build (not production-hardened).
- Email verification flow exists in API, but front-end currently uses a simplified onboarding path.
