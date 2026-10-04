"""Database models: User, Subject, Task."""
from datetime import datetime, date, timezone

from werkzeug.security import generate_password_hash, check_password_hash

from . import db


def utcnow():
    """Naive UTC timestamp (avoids deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    subjects = db.relationship("Subject", backref="user", cascade="all, delete-orphan")
    tasks = db.relationship("Task", backref="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(60), nullable=False)

    tasks = db.relationship("Task", backref="subject")

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=True)
    title = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text, default="")
    due_date = db.Column(db.Date, nullable=True)
    difficulty = db.Column(db.Integer, default=3)       # 1 (easy) .. 5 (hard)
    est_minutes = db.Column(db.Integer, default=30)     # estimated effort
    done = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    @property
    def is_overdue(self) -> bool:
        return bool(self.due_date and not self.done and self.due_date < date.today())

    def to_dict(self):
        from .services import priority_score, priority_label

        score = priority_score(self)
        return {
            "id": self.id,
            "title": self.title,
            "notes": self.notes or "",
            "subject_id": self.subject_id,
            "subject": self.subject.name if self.subject else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "difficulty": self.difficulty,
            "est_minutes": self.est_minutes,
            "done": self.done,
            "overdue": self.is_overdue,
            "priority_score": score,
            "priority": priority_label(score),
        }
