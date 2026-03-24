import os
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

import yaml
from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017")
app.config["MONGO_DB_NAME"] = os.environ.get("MONGO_DB_NAME", "taskboard")

CORS(app)

mongo_db = None


def init_db():
    global mongo_db
    uri = app.config["MONGO_URI"]
    if app.config.get("TESTING"):
        import mongomock

        client = mongomock.MongoClient()
    else:
        client = MongoClient(uri)
    mongo_db = client[app.config["MONGO_DB_NAME"]]
    mongo_db.users.create_index("email", unique=True)


def get_db():
    global mongo_db
    if mongo_db is None:
        init_db()
    return mongo_db


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)

    return wrapper


def api_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)

    return wrapper


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("board"))
    return render_template("welcome.html")


@app.route("/welcome")
def welcome_page():
    return render_template("welcome.html")


@app.route("/board")
@login_required
def board():
    return render_template("board.html")


@app.route("/info")
def info():
    return render_template("info.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/docs")
def docs_page():
    return render_template("docs.html")


@app.route("/swagger")
def swagger_ui():
    return render_template("swagger.html")


@app.route("/openapi.json")
def openapi_json():
    spec_path = Path(__file__).resolve().parent / "openapi.yaml"
    with open(spec_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    return jsonify(spec)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("board"))
    err = None
    db = get_db()
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = db.users.find_one({"email": email})
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = str(user["_id"])
            nxt = request.form.get("next") or request.args.get("next") or url_for("board")
            if not nxt.startswith("/"):
                nxt = url_for("board")
            return redirect(nxt)
        err = "wrong email or password"
    return render_template("login.html", error=err)


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("board"))
    err = None
    db = get_db()
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        if not email or "@" not in email:
            err = "enter a valid email"
        elif len(password) < 3:
            err = "password must be at least 3 characters"
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
            return redirect(url_for("board"))
    return render_template("register.html", error=err)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/tasks", methods=["GET"])
@api_login_required
def get_tasks():
    db = get_db()
    uid = session["user_id"]
    cur = db.tasks.find({"user_id": uid}).sort("created_at", 1)
    return jsonify(
        [{"id": str(t["_id"]), "title": t["title"], "status": t["status"]} for t in cur]
    )


@app.route("/tasks", methods=["POST"])
@api_login_required
def create_task():
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
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


@app.route("/tasks/<task_id>", methods=["PATCH"])
@api_login_required
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
        updates["status"] = data["status"]
    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "title required"}), 400
        updates["title"] = title

    if not updates:
        return jsonify({"error": "no fields"}), 400

    db.tasks.update_one({"_id": oid}, {"$set": updates})
    updated = db.tasks.find_one({"_id": oid})
    return jsonify(
        {
            "id": str(updated["_id"]),
            "title": updated["title"],
            "status": updated["status"],
        }
    )


@app.route("/tasks/<task_id>", methods=["DELETE"])
@api_login_required
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


if __name__ == "__main__":
    app.run(debug=True)
