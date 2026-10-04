# StudyFlow - Smart Study Planner

StudyFlow is a Flask web application that helps students organise subjects and tasks.
Its **smart priority engine** ranks pending work by due date, difficulty and estimated effort,
so the dashboard always shows what to study next.

## Features
- User registration and login (salted password hashes, session auth, CSRF protection)
- Subjects and tasks with full create / read / update / delete
- Smart priority score and High / Medium / Low labels
- Dashboard: totals, overdue count, completion rate, minutes studied, progress per subject
- JSON REST API under `/api`
- 29 automated tests (pytest)

## Tech stack
Python 3.10+, Flask, Flask-SQLAlchemy (SQLite), Jinja2, pytest.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py                      # open http://127.0.0.1:5000
```
Set `SECRET_KEY` (and optionally `DATABASE_URL`) as environment variables outside development.

## Run the tests
```bash
python -m pytest -q
```

## Project structure
```
studyflow/
  app/
    __init__.py     application factory, CSRF, error handlers
    models.py       User, Subject, Task
    services.py     validation, priority scoring, statistics
    auth.py         register / login / logout, login_required
    routes.py       HTML pages
    api.py          JSON REST API
    templates/      Jinja2 templates
    static/         CSS
  tests/            pytest suite (services, auth, tasks, API)
  docs/             architecture and developer guide
  config.py  run.py  requirements.txt
```

## REST API (log in first; session cookie)
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/tasks` (`?sort=priority`) | List tasks |
| POST | `/api/tasks` | Create a task (JSON body) |
| GET / PUT / DELETE | `/api/tasks/<id>` | Read, update, delete |
| GET | `/api/stats` | Dashboard statistics |

Example body: `{"title": "Revise DBMS", "difficulty": 4, "est_minutes": 90, "due_date": "2026-11-20"}`

## Priority formula
`score = urgency + difficulty x 6 + min(minutes / 15, 10)`
Urgency is 100 if overdue, else `max(0, 60 - 6 x days_left)`, and 10 when there is no due date.
Score >= 70 is High, >= 40 is Medium, otherwise Low. Completed tasks score 0.
