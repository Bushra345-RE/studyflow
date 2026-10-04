"""Business logic kept separate from routes: validation, priority scoring, statistics."""
from datetime import date, datetime

MAX_TITLE = 120


def parse_date(value):
    """Return a date from an ISO string (YYYY-MM-DD), None for blank, raise ValueError if invalid."""
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def validate_task_data(data, user_subject_ids=()):
    """Validate raw task input (form or JSON). Returns (clean_dict, errors_list)."""
    errors, clean = [], {}

    title = (data.get("title") or "").strip()
    if not title:
        errors.append("Title is required.")
    elif len(title) > MAX_TITLE:
        errors.append(f"Title must be at most {MAX_TITLE} characters.")
    clean["title"] = title

    clean["notes"] = (data.get("notes") or "").strip()[:2000]

    try:
        clean["due_date"] = parse_date(data.get("due_date"))
    except ValueError:
        errors.append("Due date must be in YYYY-MM-DD format.")

    try:
        difficulty = int(data.get("difficulty", 3) or 3)
        if not 1 <= difficulty <= 5:
            raise ValueError
        clean["difficulty"] = difficulty
    except (TypeError, ValueError):
        errors.append("Difficulty must be a whole number from 1 to 5.")

    try:
        minutes = int(data.get("est_minutes", 30) or 30)
        if not 5 <= minutes <= 600:
            raise ValueError
        clean["est_minutes"] = minutes
    except (TypeError, ValueError):
        errors.append("Estimated minutes must be a whole number from 5 to 600.")

    subject_id = data.get("subject_id")
    if subject_id in (None, "", 0, "0"):
        clean["subject_id"] = None
    else:
        try:
            subject_id = int(subject_id)
        except (TypeError, ValueError):
            errors.append("Invalid subject.")
        else:
            if subject_id not in user_subject_ids:
                errors.append("Subject does not exist.")
            else:
                clean["subject_id"] = subject_id
    return clean, errors


def priority_score(task, today=None):
    """Smart priority score (0-140). Higher means do it sooner.

    urgency (0-100): overdue = 100, otherwise falls by 6 points per day remaining;
                     tasks with no due date get a low baseline of 10.
    difficulty (6-30): harder tasks need an earlier start.
    effort (0-10):  longer tasks get a small boost.
    Completed tasks always score 0.
    """
    if task.done:
        return 0
    today = today or date.today()
    if task.due_date is None:
        urgency = 10
    else:
        days_left = (task.due_date - today).days
        urgency = 100 if days_left < 0 else max(0, 60 - days_left * 6)
    difficulty = (task.difficulty or 3) * 6
    effort = min((task.est_minutes or 30) / 15, 10)
    return round(urgency + difficulty + effort, 1)


def priority_label(score):
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def ranked_tasks(tasks, limit=None):
    """Pending tasks sorted by priority score, highest first."""
    pending = [t for t in tasks if not t.done]
    pending.sort(key=priority_score, reverse=True)
    return pending[:limit] if limit else pending


def compute_stats(tasks):
    total = len(tasks)
    done = [t for t in tasks if t.done]
    pending = total - len(done)
    overdue = sum(1 for t in tasks if t.is_overdue)
    by_subject = {}
    for t in tasks:
        name = t.subject.name if t.subject else "General"
        entry = by_subject.setdefault(name, {"total": 0, "done": 0})
        entry["total"] += 1
        entry["done"] += 1 if t.done else 0
    return {
        "total": total,
        "done": len(done),
        "pending": pending,
        "overdue": overdue,
        "completion_rate": round(len(done) / total * 100) if total else 0,
        "minutes_completed": sum(t.est_minutes or 0 for t in done),
        "by_subject": by_subject,
    }
