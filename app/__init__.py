"""StudyFlow application factory."""
import secrets

from flask import Flask, jsonify, render_template, request, session, abort
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)

    from .auth import auth_bp
    from .routes import main_bp
    from .api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # ---- CSRF protection for HTML form posts ----
    def csrf_token():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        return session["_csrf"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def check_csrf():
        if not app.config.get("CSRF_ENABLED", True):
            return
        if request.method == "POST" and not request.path.startswith("/api/"):
            sent = request.form.get("csrf_token", "")
            if not sent or sent != session.get("_csrf"):
                abort(400, description="Invalid or missing CSRF token.")

    # ---- Error handlers ----
    @app.errorhandler(404)
    def not_found(err):
        if request.path.startswith("/api/"):
            return jsonify(error="Not found"), 404
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(400)
    def bad_request(err):
        if request.path.startswith("/api/"):
            return jsonify(error=getattr(err, "description", "Bad request")), 400
        return render_template("error.html", code=400, message=err.description), 400

    with app.app_context():
        db.create_all()

    return app
