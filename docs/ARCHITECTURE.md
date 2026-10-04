# StudyFlow - Architecture & Developer Guide

## Layers
1. **Presentation** - Jinja2 templates (`app/templates`) and `static/style.css`.
2. **Controllers** - `routes.py` (HTML) and `api.py` (JSON). They only handle HTTP concerns.
3. **Business logic** - `services.py`: validation, priority scoring, statistics. No Flask imports,
   so it is easy to unit test.
4. **Data** - `models.py` with SQLAlchemy models on SQLite.

## Data model
- `User (id, username*, password_hash, created_at)`
- `Subject (id, user_id -> User, name)`
- `Task (id, user_id -> User, subject_id -> Subject?, title, notes, due_date?, difficulty 1-5,
  est_minutes 5-600, done, completed_at?, created_at)`

Deleting a user cascades to their subjects and tasks. Deleting a subject keeps its tasks (set to General).

## Key design decisions
- **Application factory** (`create_app`) so tests build isolated apps with an in-memory database.
- **Single validation function** shared by the HTML forms and the API, so both enforce identical rules.
- **Ownership checks** on every task/subject lookup; other users' records return 404, not 403,
  to avoid leaking their existence.
- **CSRF**: every HTML POST needs a session-bound token. API routes require a JSON body, which
  browsers cannot send cross-site without a CORS preflight.
- **Passwords** use Werkzeug salted hashing; the session is cleared on login to prevent fixation.

## How to extend
- Add a model in `models.py`, rules in `services.py`, then a route and template.
- Change the ranking by editing `priority_score` and its tests in `tests/test_services.py`.
- For production: set `SECRET_KEY`, use PostgreSQL via `DATABASE_URL`, serve with gunicorn behind HTTPS,
  and set `SESSION_COOKIE_SECURE = True`.

## Known limitations
- No password reset or email verification.
- Schema changes need a migration tool (e.g. Flask-Migrate); not included.
- No rate limiting on login attempts.
