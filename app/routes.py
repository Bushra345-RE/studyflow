"""HTML routes: dashboard, subjects, and tasks."""
from flask import (Blueprint, abort, flash, g, redirect, render_template,
                   request, url_for)

from . import db
from .auth import login_required
from .models import Subject, Task, utcnow
from .services import (compute_stats, priority_label, priority_score,
                       ranked_tasks, validate_task_data)

main_bp = Blueprint("main", __name__)


def _own_task_or_404(task_id):
    task = db.session.get(Task, task_id)
    if task is None or task.user_id != g.user.id:
        abort(404)
    return task


def _subject_ids():
    return {s.id for s in Subject.query.filter_by(user_id=g.user.id)}


@main_bp.route("/")
def index():
    return redirect(url_for("main.dashboard" if g.user else "auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=g.user.id).all()
    return render_template(
        "dashboard.html",
        stats=compute_stats(tasks),
        focus=ranked_tasks(tasks, limit=5),
        score=priority_score,
        label=priority_label,
    )


@main_bp.route("/subjects", methods=["GET", "POST"])
@login_required
def subjects():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name or len(name) > 60:
            flash("Subject name is required (max 60 characters).", "error")
        elif Subject.query.filter_by(user_id=g.user.id, name=name).first():
            flash("You already have that subject.", "error")
        else:
            db.session.add(Subject(user_id=g.user.id, name=name))
            db.session.commit()
            flash("Subject added.", "ok")
        return redirect(url_for("main.subjects"))
    items = Subject.query.filter_by(user_id=g.user.id).order_by(Subject.name).all()
    return render_template("subjects.html", subjects=items)


@main_bp.route("/subjects/<int:subject_id>/delete", methods=["POST"])
@login_required
def delete_subject(subject_id):
    subject = db.session.get(Subject, subject_id)
    if subject is None or subject.user_id != g.user.id:
        abort(404)
    Task.query.filter_by(subject_id=subject.id).update({"subject_id": None})
    db.session.delete(subject)
    db.session.commit()
    flash("Subject deleted. Its tasks were kept as General.", "ok")
    return redirect(url_for("main.subjects"))


@main_bp.route("/tasks")
@login_required
def tasks():
    query = Task.query.filter_by(user_id=g.user.id)
    status = request.args.get("status", "all")
    if status == "pending":
        query = query.filter_by(done=False)
    elif status == "done":
        query = query.filter_by(done=True)
    subject_id = request.args.get("subject", type=int)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    items = sorted(query.all(), key=lambda t: (t.done, -priority_score(t)))
    subjects_ = Subject.query.filter_by(user_id=g.user.id).all()
    return render_template("tasks.html", tasks=items, subjects=subjects_, status=status,
                           subject_id=subject_id, score=priority_score, label=priority_label)


@main_bp.route("/tasks/new", methods=["GET", "POST"])
@login_required
def new_task():
    subjects_ = Subject.query.filter_by(user_id=g.user.id).all()
    if request.method == "POST":
        clean, errors = validate_task_data(request.form, _subject_ids())
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("task_form.html", task=request.form, subjects=subjects_, mode="new"), 400
        db.session.add(Task(user_id=g.user.id, **clean))
        db.session.commit()
        flash("Task created.", "ok")
        return redirect(url_for("main.tasks"))
    return render_template("task_form.html", task={}, subjects=subjects_, mode="new")


@main_bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = _own_task_or_404(task_id)
    subjects_ = Subject.query.filter_by(user_id=g.user.id).all()
    if request.method == "POST":
        clean, errors = validate_task_data(request.form, _subject_ids())
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("task_form.html", task=request.form, subjects=subjects_,
                                   mode="edit", task_id=task.id), 400
        for key, value in clean.items():
            setattr(task, key, value)
        db.session.commit()
        flash("Task updated.", "ok")
        return redirect(url_for("main.tasks"))
    return render_template("task_form.html", task=task, subjects=subjects_, mode="edit", task_id=task.id)


@main_bp.route("/tasks/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_task(task_id):
    task = _own_task_or_404(task_id)
    task.done = not task.done
    task.completed_at = utcnow() if task.done else None
    db.session.commit()
    return redirect(request.referrer or url_for("main.tasks"))


@main_bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    task = _own_task_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "ok")
    return redirect(url_for("main.tasks"))
