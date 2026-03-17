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

```
date-drop/
├── app.py                      # Flask app, routes, and API
├── requirements.txt
├── .env.example
├── templates/
│   ├── index.html              # Landing page
│   ├── questions.html          # Onboarding questionnaire
│   ├── home.html               # Matches home page
│   └── cupid.html              # Cupid page
├── static/
│   ├── css/
│   │   ├── base.css            # Shared reset, logo, topbar styles
│   │   ├── landing.css         # Landing page styles
│   │   ├── questions.css       # Questionnaire styles
│   │   ├── home.css            # Home page styles
│   │   └── cupid.css           # Cupid page styles
│   ├── js/
│   │   ├── landing.js          # Landing page logic
│   │   ├── questions.js        # Questionnaire logic
│   │   └── cupid.js            # Cupid page logic
│   └── images/
│       └── questions*.jpg      # Question reference screenshots
```

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
