def register(client, email="a@b.c", password="secret"):
    return client.post(
        "/register",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def test_tasks_requires_auth(client):
    r = client.get("/tasks")
    assert r.status_code == 401


def test_get_tasks_empty(client):
    register(client)
    r = client.get("/tasks")
    assert r.status_code == 200
    assert r.get_json() == []


def test_create_and_list_task(client):
    register(client)
    r = client.post(
        "/tasks",
        json={"title": "buy milk"},
        content_type="application/json",
    )
    assert r.status_code == 201
    body = r.get_json()
    assert body["title"] == "buy milk"
    assert body["status"] == "todo"
    tid = body["id"]

    r = client.get("/tasks")
    assert r.status_code == 200
    tasks = r.get_json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == tid
    assert tasks[0]["title"] == "buy milk"


def test_patch_status(client):
    register(client)
    r = client.post("/tasks", json={"title": "x"}, content_type="application/json")
    tid = r.get_json()["id"]

    r = client.patch(f"/tasks/{tid}", json={"status": "doing"})
    assert r.status_code == 200
    assert r.get_json()["status"] == "doing"

    r = client.get("/tasks")
    task = next(t for t in r.get_json() if t["id"] == tid)
    assert task["status"] == "doing"


def test_patch_rename(client):
    register(client)
    r = client.post("/tasks", json={"title": "old"}, content_type="application/json")
    tid = r.get_json()["id"]

    r = client.patch(f"/tasks/{tid}", json={"title": "new title"})
    assert r.status_code == 200
    assert r.get_json()["title"] == "new title"

    r = client.get("/tasks")
    task = next(t for t in r.get_json() if t["id"] == tid)
    assert task["title"] == "new title"


def test_openapi_json(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    data = r.get_json()
    assert data["openapi"] == "3.0.3"
    assert "/tasks" in data["paths"]


def test_delete_task(client):
    register(client)
    r = client.post("/tasks", json={"title": "tmp"}, content_type="application/json")
    tid = r.get_json()["id"]

    r = client.delete(f"/tasks/{tid}")
    assert r.status_code == 200

    r = client.get("/tasks")
    assert r.get_json() == []


def test_users_see_own_tasks_only(client):
    register(client, email="u1@test.com", password="secret")
    client.post("/tasks", json={"title": "mine"}, content_type="application/json")

    client.get("/logout")
    register(client, email="u2@test.com", password="secret")
    r = client.get("/tasks")
    assert r.get_json() == []
