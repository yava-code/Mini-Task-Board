import os
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
db = SQLAlchemy(app)
CORS(app)


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
def create_task():
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
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

    app.run(debug=True)
