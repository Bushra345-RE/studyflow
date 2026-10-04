from datetime import date, timedelta
from types import SimpleNamespace

from app.services import (compute_stats, priority_label, priority_score,
                          ranked_tasks, validate_task_data)


def make(due=None, difficulty=3, minutes=30, done=False, subject=None):
    t = SimpleNamespace(due_date=due, difficulty=difficulty, est_minutes=minutes, done=done,
                        subject=subject)
    t.is_overdue = bool(due and not done and due < date.today())
    return t


def test_overdue_task_scores_higher_than_future_task():
    overdue = make(due=date.today() - timedelta(days=1))
    later = make(due=date.today() + timedelta(days=10))
    assert priority_score(overdue) > priority_score(later)


def test_no_due_date_uses_low_baseline():
    assert priority_score(make()) < 40


def test_completed_task_scores_zero():
    assert priority_score(make(due=date.today(), done=True)) == 0


def test_harder_task_scores_higher_with_same_due_date():
    due = date.today() + timedelta(days=3)
    assert priority_score(make(due=due, difficulty=5)) > priority_score(make(due=due, difficulty=1))


def test_priority_labels():
    assert priority_label(90) == "High"
    assert priority_label(50) == "Medium"
    assert priority_label(10) == "Low"


def test_ranked_tasks_orders_and_excludes_done():
    urgent = make(due=date.today())
    relaxed = make(due=date.today() + timedelta(days=30))
    finished = make(done=True)
    assert ranked_tasks([relaxed, finished, urgent]) == [urgent, relaxed]


def test_validation_accepts_valid_data():
    clean, errors = validate_task_data(
        {"title": " Read chapter 4 ", "difficulty": "4", "est_minutes": "45", "due_date": "2026-12-01"})
    assert errors == []
    assert clean["title"] == "Read chapter 4" and clean["difficulty"] == 4


def test_validation_rejects_bad_data():
    _, errors = validate_task_data(
        {"title": "", "difficulty": "9", "est_minutes": "abc", "due_date": "01/12/2026"})
    assert len(errors) == 4


def test_validation_rejects_foreign_subject():
    _, errors = validate_task_data({"title": "x", "subject_id": "99"}, user_subject_ids={1, 2})
    assert "Subject does not exist." in errors


def test_stats_empty_and_populated():
    assert compute_stats([])["completion_rate"] == 0
    stats = compute_stats([make(done=True, minutes=60), make(due=date.today() - timedelta(days=2))])
    assert stats["total"] == 2 and stats["done"] == 1 and stats["overdue"] == 1
    assert stats["completion_rate"] == 50 and stats["minutes_completed"] == 60
