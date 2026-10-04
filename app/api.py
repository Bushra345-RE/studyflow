"""JSON REST API (session-authenticated)."""
from flask import Blueprint, g, jsonify, request

from . import db
from .auth import login_required
from .models import Subject, Task, utcnow
from .services import compute_stats, ranked_tasks, validate_task_data

api_bp = Blueprint("api", __name__)


def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def _subject_ids():
    return {s.id for s in Subject.query.filter_by(user_id=g.user.id)}


def _get_task(task_id):
    task = db.session.get(Task, task_id)
    return task if task and task.user_id == g.user.id else None


@api_bp.route("/tasks", methods=["GET"])
@login_required
def list_tasks():
    tasks = Task.query.filter_by(user_id=g.user.id).all()
    if request.args.get("sort") == "priority":
        tasks = ranked_tasks(tasks) + [t for t in tasks if t.done]
    return jsonify([t.to_dict() for t in tasks])


@api_bp.route("/tasks", methods=["POST"])
@login_required
def create_task():
    data = _json_body()
    if data is None:
        return jsonify(error="Request body must be a JSON object"), 400
    clean, errors = validate_task_data(data, _subject_ids())
    if errors:
        return jsonify(errors=errors), 422
    task = Task(user_id=g.user.id, **clean)
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


@api_bp.route("/tasks/<int:task_id>", methods=["GET"])
@login_required
def get_task(task_id):
    task = _get_task(task_id)
    return (jsonify(task.to_dict()), 200) if task else (jsonify(error="Not found"), 404)


@api_bp.route("/tasks/<int:task_id>", methods=["PUT"])
@login_required
def update_task(task_id):
    task = _get_task(task_id)
    if task is None:
        return jsonify(error="Not found"), 404
    data = _json_body()
    if data is None:
        return jsonify(error="Request body must be a JSON object"), 400
    merged = {**task.to_dict(), **data}
    clean, errors = validate_task_data(merged, _subject_ids())
    if errors:
        return jsonify(errors=errors), 422
    for key, value in clean.items():
        setattr(task, key, value)
    if "done" in data:
        task.done = bool(data["done"])
        task.completed_at = utcnow() if task.done else None
    db.session.commit()
    return jsonify(task.to_dict())


@api_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    task = _get_task(task_id)
    if task is None:
        return jsonify(error="Not found"), 404
    db.session.delete(task)
    db.session.commit()
    return "", 204


@api_bp.route("/stats", methods=["GET"])
@login_required
def stats():
    return jsonify(compute_stats(Task.query.filter_by(user_id=g.user.id).all()))
