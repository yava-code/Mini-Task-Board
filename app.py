import os
from datetime import datetime, timezone
from functools import wraps

from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, jsonify, render_template, request, session
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
        if "user_id" not in session:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)

    return wrapper


def current_user_id():
    return session.get("user_id")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/info")
def info():
    return render_template("info.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or "@" not in email:
        return jsonify({"error": "invalid email"}), 400
    if len(password) < 3:
        return jsonify({"error": "password too short"}), 400

    db = get_db()
    if db.users.find_one({"email": email}):
        return jsonify({"error": "email taken"}), 409

    uid = ObjectId()
    db.users.insert_one(
        {
            "_id": uid,
            "email": email,
            "password_hash": generate_password_hash(password),
        }
    )
    session["user_id"] = str(uid)
    return jsonify({"email": email}), 201


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    db = get_db()
    user = db.users.find_one({"email": email})
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "invalid credentials"}), 401

    session["user_id"] = str(user["_id"])
    return jsonify({"email": user["email"]})


@app.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/auth/me", methods=["GET"])
def me():
    uid = current_user_id()
    if not uid:
        return jsonify({"error": "unauthorized"}), 401
    db = get_db()
    try:
        user = db.users.find_one({"_id": ObjectId(uid)})
    except InvalidId:
        return jsonify({"error": "unauthorized"}), 401
    if not user:
        session.clear()
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"email": user["email"]})


def task_to_json(doc):
    return {
        "id": str(doc["_id"]),
        "title": doc["title"],
        "status": doc["status"],
    }


@app.route("/tasks", methods=["GET"])
@login_required
def get_tasks():
    db = get_db()
    uid = current_user_id()
    cur = db.tasks.find({"user_id": uid}).sort("created_at", 1)
    return jsonify([task_to_json(t) for t in cur])


@app.route("/tasks", methods=["POST"])
@login_required
def create_task():
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400

    db = get_db()
    uid = current_user_id()
    doc = {
        "user_id": uid,
        "title": title,
        "status": "todo",
        "created_at": datetime.now(timezone.utc),
    }
    res = db.tasks.insert_one(doc)
    doc["_id"] = res.inserted_id
    return jsonify(task_to_json(doc)), 201


@app.route("/tasks/<task_id>", methods=["PATCH"])
@login_required
def update_task(task_id):
    try:
        oid = ObjectId(task_id)
    except InvalidId:
        return jsonify({"error": "not found"}), 404

    db = get_db()
    uid = current_user_id()
    task = db.tasks.find_one({"_id": oid, "user_id": uid})
    if not task:
        return jsonify({"error": "not found"}), 404

    data = request.get_json() or {}
    if "status" in data:
        db.tasks.update_one({"_id": oid}, {"$set": {"status": data["status"]}})
    return jsonify({"message": "ok"})


@app.route("/tasks/<task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    try:
        oid = ObjectId(task_id)
    except InvalidId:
        return jsonify({"error": "not found"}), 404

    db = get_db()
    uid = current_user_id()
    res = db.tasks.delete_one({"_id": oid, "user_id": uid})
    if res.deleted_count == 0:
        return jsonify({"error": "not found"}), 404
    return jsonify({"message": "deleted"})


if __name__ == "__main__":
    app.run(debug=True)
