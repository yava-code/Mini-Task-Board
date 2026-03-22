def register(client, email="a@b.c", password="secret"):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password},
        content_type="application/json",
    )


def test_tasks_requires_auth(client):
    r = client.get("/tasks")
    assert r.status_code == 401


def test_get_tasks_empty(client):
    assert register(client).status_code == 201
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

    r = client.get("/tasks")
    task = next(t for t in r.get_json() if t["id"] == tid)
    assert task["status"] == "doing"


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

    register(client, email="u2@test.com", password="secret")
    r = client.get("/tasks")
    assert r.get_json() == []
