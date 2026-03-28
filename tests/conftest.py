import pytest

from app import app, get_db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    app.extensions.pop("mongo_db", None)
    with app.app_context():
        db = get_db()
        db.users.delete_many({})
        db.tasks.delete_many({})
        db.users.create_index("email", unique=True)
    with app.test_client() as c:
        yield c
