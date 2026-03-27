import os
import re
import secrets
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

import yaml
from bson import ObjectId
from bson.errors import InvalidId
from flask import (
    Blueprint,
    Flask,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash

TASK_STATUS = {"todo", "doing", "done"}
MAX_TITLE_LEN = 200
MIN_PASSWORD_LEN = 8


def init_db():
    app = current_app._get_current_object()
    uri = os.environ.get(
        "MONGO_URL", app.config.get("MONGO_URI", "mongodb://localhost:27017/")
    )
    if app.config.get("TESTING"):
        import mongomock

        client = mongomock.MongoClient()
    else:
        client = MongoClient(uri)
    db = client[app.config.get("MONGO_DB_NAME", "mytaskdb")]
    db.users.create_index("email", unique=True)
    db.tasks.create_index([("user_id", 1), ("created_at", 1)])
    app.extensions["mongo_db"] = db


def get_db():
    db = current_app.extensions.get("mongo_db")
    if db is None:
        init_db()
        db = current_app.extensions["mongo_db"]
    return db


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)

    return wrapper


def api_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)

    return wrapper


def api_csrf_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-CSRF-Token", "")
        if not is_valid_csrf(token):
            return jsonify({"error": "bad csrf token"}), 403
        return f(*args, **kwargs)

    return wrapper


def get_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def is_valid_csrf(token):
    sess_token = session.get("csrf_token")
    if not token or not sess_token:
        return False
    return secrets.compare_digest(token, sess_token)


main_bp = Blueprint("main", __name__)
auth_bp = Blueprint("auth", __name__)
tasks_bp = Blueprint("tasks", __name__)


@main_bp.route("/", endpoint="index")
def index():
    if session.get("user_id"):
        return redirect(url_for("main.board"))
    return render_template("welcome.html")


@main_bp.route("/welcome", endpoint="welcome_page")
def welcome_page():
    return render_template("welcome.html")


@main_bp.route("/board", endpoint="board")
@login_required
def board():
    return render_template("board.html", csrf_token=get_csrf_token())


@main_bp.route("/info", endpoint="info")
def info():
    return render_template("info.html")


@main_bp.route("/contact", endpoint="contact")
def contact():
    return render_template("contact.html")


@main_bp.route("/docs", endpoint="docs_page")
def docs_page():
    return render_template("docs.html")


@main_bp.route("/swagger", endpoint="swagger_ui")
def swagger_ui():
    return render_template("swagger.html")


@main_bp.route("/openapi.json", endpoint="openapi_json")
def openapi_json():
    spec_path = Path(__file__).resolve().parent / "openapi.yaml"
    with open(spec_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    return jsonify(spec)


@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    if session.get("user_id"):
        return redirect(url_for("main.board"))
    err = None
    db = get_db()
    if request.method == "POST":
        csrf_token = request.form.get("csrf_token", "")
        if not is_valid_csrf(csrf_token):
            err = "session expired, refresh and try again"
            return render_template("login.html", error=err, csrf_token=get_csrf_token())
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = db.users.find_one({"email": email})
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = str(user["_id"])
            nxt = (
                request.form.get("next")
                or request.args.get("next")
                or url_for("main.board")
            )
            if not nxt.startswith("/"):
                nxt = url_for("main.board")
            return redirect(nxt)
        err = "wrong email or password"
    return render_template("login.html", error=err, csrf_token=get_csrf_token())


@auth_bp.route("/register", methods=["GET", "POST"], endpoint="register")
def register():
    if session.get("user_id"):
        return redirect(url_for("main.board"))
    err = None
    db = get_db()
    if request.method == "POST":
        csrf_token = request.form.get("csrf_token", "")
        if not is_valid_csrf(csrf_token):
            err = "session expired, refresh and try again"
            return render_template(
                "register.html", error=err, csrf_token=get_csrf_token()
            )
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_pattern, email):
            err = "enter a valid email"
        elif len(password) < MIN_PASSWORD_LEN:
            err = f"password must be at least {MIN_PASSWORD_LEN} characters"
        elif db.users.find_one({"email": email}):
            err = "that email is already registered"
        else:
            uid = ObjectId()
            db.users.insert_one(
                {
                    "_id": uid,
                    "email": email,
                    "password_hash": generate_password_hash(password),
                }
            )
            session["user_id"] = str(uid)
            return redirect(url_for("main.board"))
    return render_template("register.html", error=err, csrf_token=get_csrf_token())


@auth_bp.route("/logout", endpoint="logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))


@tasks_bp.route("/tasks", methods=["GET"], endpoint="get_tasks")
@api_login_required
def get_tasks():
    db = get_db()
    uid = session["user_id"]
    cur = db.tasks.find({"user_id": uid}).sort("created_at", 1)
    return jsonify(
        [{"id": str(t["_id"]), "title": t["title"], "status": t["status"]} for t in cur]
    )


@tasks_bp.route("/tasks", methods=["POST"], endpoint="create_task")
@api_login_required
@api_csrf_required
def create_task():
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
    if len(title) > MAX_TITLE_LEN:
        return jsonify({"error": f"title too long (max {MAX_TITLE_LEN})"}), 400
    db = get_db()
    doc = {
        "user_id": session["user_id"],
        "title": title,
        "status": "todo",
        "created_at": datetime.now(timezone.utc),
    }
    res = db.tasks.insert_one(doc)
    return (
        jsonify(
            {"id": str(res.inserted_id), "title": title, "status": "todo"}
        ),
        201,
    )


@tasks_bp.route("/tasks/<task_id>", methods=["PATCH"], endpoint="update_task")
@api_login_required
@api_csrf_required
def update_task(task_id):
    try:
        oid = ObjectId(task_id)
    except InvalidId:
        return jsonify({"error": "not found"}), 404

    db = get_db()
    uid = session["user_id"]
    task = db.tasks.find_one({"_id": oid, "user_id": uid})
    if not task:
        return jsonify({"error": "not found"}), 404

    data = request.get_json() or {}
    if not data:
        return jsonify({"error": "no fields"}), 400

    updates = {}
    if "status" in data:
        status = (data.get("status") or "").strip()
        if status not in TASK_STATUS:
            return jsonify({"error": "status must be todo, doing or done"}), 400
        updates["status"] = status
    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "title required"}), 400
        if len(title) > MAX_TITLE_LEN:
            return jsonify({"error": f"title too long (max {MAX_TITLE_LEN})"}), 400
        updates["title"] = title

    if not updates:
        return jsonify({"error": "no fields"}), 400

    db.tasks.update_one({"_id": oid, "user_id": uid}, {"$set": updates})
    updated = db.tasks.find_one({"_id": oid, "user_id": uid})
    return jsonify(
        {
            "id": str(updated["_id"]),
            "title": updated["title"],
            "status": updated["status"],
        }
    )


@tasks_bp.route("/tasks/<task_id>", methods=["DELETE"], endpoint="delete_task")
@api_login_required
@api_csrf_required
def delete_task(task_id):
    try:
        oid = ObjectId(task_id)
    except InvalidId:
        return jsonify({"error": "not found"}), 404

    db = get_db()
    uid = session["user_id"]
    res = db.tasks.delete_one({"_id": oid, "user_id": uid})
    if res.deleted_count == 0:
        return jsonify({"error": "not found"}), 404
    return jsonify({"message": "deleted"})


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017")
    app.config["MONGO_DB_NAME"] = os.environ.get("MONGO_DB_NAME", "taskboard")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get(
        "SESSION_COOKIE_SECURE", ""
    ).lower() in {"1", "true", "yes"}
    app.config["SESSION_COOKIE_SAMESITE"] = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")

    if (
        os.environ.get("FLASK_ENV") == "production"
        and app.config["SECRET_KEY"] == "dev-secret-change-me"
    ):
        raise RuntimeError("set SECRET_KEY in production")

    cors_origins = [
        o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
    ]
    if cors_origins:
        CORS(
            app,
            resources={r"/tasks*": {"origins": cors_origins}},
            supports_credentials=True,
        )

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
