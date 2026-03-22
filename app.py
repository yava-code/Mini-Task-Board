import os
from datetime import datetime, timezone
from functools import wraps

<<<<<<< HEAD
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
db = SQLAlchemy(app)
=======
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

>>>>>>> b4c50dfdc5fd813fc94ac55865b3fe473fef2dd4
CORS(app)

mongo_db = None

<<<<<<< HEAD
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default="todo")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

=======

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

>>>>>>> b4c50dfdc5fd813fc94ac55865b3fe473fef2dd4

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
<<<<<<< HEAD
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)

    return wrapper


def api_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
=======
        if "user_id" not in session:
>>>>>>> b4c50dfdc5fd813fc94ac55865b3fe473fef2dd4
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)

    return wrapper


<<<<<<< HEAD
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


=======
def current_user_id():
    return session.get("user_id")


@app.route("/")
def index():
    return render_template("index.html")


>>>>>>> b4c50dfdc5fd813fc94ac55865b3fe473fef2dd4
@app.route("/info")
def info():
    return render_template("info.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


<<<<<<< HEAD
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("board"))
    err = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            nxt = request.form.get("next") or request.args.get("next") or url_for("board")
            if not nxt.startswith("/"):
                nxt = url_for("board")
            return redirect(nxt)
        err = "неверный email или пароль"
    return render_template("login.html", error=err)


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("board"))
    err = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        if not email or "@" not in email:
            err = "нужен нормальный email"
        elif len(password) < 3:
            err = "пароль минимум 3 символа"
        elif User.query.filter_by(email=email).first():
            err = "такой email уже есть"
        else:
            u = User(
                email=email,
                password_hash=generate_password_hash(password),
            )
            db.session.add(u)
            db.session.commit()
            session["user_id"] = u.id
            return redirect(url_for("board"))
    return render_template("register.html", error=err)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/tasks", methods=["GET"])
@api_login_required
def get_tasks():
    uid = session["user_id"]
    tasks = Task.query.filter_by(user_id=uid).order_by(Task.created_at).all()
    return jsonify([{"id": t.id, "title": t.title, "status": t.status} for t in tasks])


@app.route("/tasks", methods=["POST"])
@api_login_required
=======
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
>>>>>>> b4c50dfdc5fd813fc94ac55865b3fe473fef2dd4
def create_task():
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
<<<<<<< HEAD
    t = Task(title=title, user_id=session["user_id"])
    db.session.add(t)
    db.session.commit()
    return jsonify({"id": t.id, "title": t.title, "status": t.status}), 201


@app.route("/tasks/<int:id>", methods=["PATCH"])
@api_login_required
def update_task(id):
    uid = session["user_id"]
    task = Task.query.get_or_404(id)
    if task.user_id != uid:
        abort(404)
    data = request.get_json() or {}
    if "status" in data:
        task.status = data["status"]
    db.session.commit()
    return jsonify({"message": "ok"})


@app.route("/tasks/<int:id>", methods=["DELETE"])
@api_login_required
def delete_task(id):
    uid = session["user_id"]
    task = Task.query.get_or_404(id)
    if task.user_id != uid:
        abort(404)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "deleted"})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

=======

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
>>>>>>> b4c50dfdc5fd813fc94ac55865b3fe473fef2dd4
    app.run(debug=True)
