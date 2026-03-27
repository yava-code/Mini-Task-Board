import re


def get_csrf(client, path):
    r = client.get(path)
    html = r.get_data(as_text=True)
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert m
    return m.group(1)


def api_headers(client):
    r = client.get("/board")
    html = r.get_data(as_text=True)
    m = re.search(r'data-csrf-token="([^"]+)"', html)
    assert m
    token = m.group(1)
    return {"X-CSRF-Token": token}


def register(client, email="a@b.c", password="secret123"):
    token = get_csrf(client, "/register")
    return client.post(
        "/register",
        data={"email": email, "password": password, "csrf_token": token},
        follow_redirects=True,
    )


def test_tasks_requires_auth(client):
    r = client.get("/tasks")
    assert r.status_code == 401


def test_register_requires_csrf(client):
    r = client.post(
        "/register",
        data={"email": "x@y.z", "password": "secret123"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert "session expired" in r.get_data(as_text=True)


def test_get_tasks_empty(client):
    register(client, password="secret123")
    r = client.get("/tasks")
    assert r.status_code == 200
    assert r.get_json() == []


def test_create_and_list_task(client):
    register(client, password="secret123")
    headers = api_headers(client)
    r = client.post(
        "/tasks",
        json={"title": "buy milk"},
        headers=headers,
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
    register(client, password="secret123")
    headers = api_headers(client)
    r = client.post(
        "/tasks", json={"title": "x"}, headers=headers, content_type="application/json"
    )
    tid = r.get_json()["id"]

    r = client.patch(f"/tasks/{tid}", json={"status": "doing"}, headers=headers)
    assert r.status_code == 200
    assert r.get_json()["status"] == "doing"

    r = client.get("/tasks")
    task = next(t for t in r.get_json() if t["id"] == tid)
    assert task["status"] == "doing"


def test_patch_rename(client):
    register(client, password="secret123")
    headers = api_headers(client)
    r = client.post(
        "/tasks", json={"title": "old"}, headers=headers, content_type="application/json"
    )
    tid = r.get_json()["id"]

    r = client.patch(f"/tasks/{tid}", json={"title": "new title"}, headers=headers)
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
    register(client, password="secret123")
    headers = api_headers(client)
    r = client.post(
        "/tasks", json={"title": "tmp"}, headers=headers, content_type="application/json"
    )
    tid = r.get_json()["id"]

    r = client.delete(f"/tasks/{tid}", headers=headers)
    assert r.status_code == 200

    r = client.get("/tasks")
    assert r.get_json() == []


def test_users_see_own_tasks_only(client):
    register(client, email="u1@test.com", password="secret123")
    headers = api_headers(client)
    client.post("/tasks", json={"title": "mine"}, headers=headers, content_type="application/json")

    client.get("/logout")
    register(client, email="u2@test.com", password="secret123")
    r = client.get("/tasks")
    assert r.get_json() == []


def test_patch_invalid_status(client):
    register(client, password="secret123")
    headers = api_headers(client)
    r = client.post(
        "/tasks", json={"title": "x"}, headers=headers, content_type="application/json"
    )
    tid = r.get_json()["id"]

    r = client.patch(f"/tasks/{tid}", json={"status": "abc"}, headers=headers)
    assert r.status_code == 400
    assert "status must be" in r.get_json()["error"]


def test_title_too_long(client):
    register(client, password="secret123")
    headers = api_headers(client)
    long_title = "x" * 201

    r = client.post(
        "/tasks",
        json={"title": long_title},
        headers=headers,
        content_type="application/json",
    )
    assert r.status_code == 400
    assert "title too long" in r.get_json()["error"]


def test_user_cannot_patch_foreign_task(client):
    register(client, email="u1@test.com", password="secret123")
    headers_u1 = api_headers(client)
    r = client.post(
        "/tasks",
        json={"title": "mine"},
        headers=headers_u1,
        content_type="application/json",
    )
    tid = r.get_json()["id"]

    client.get("/logout")
    register(client, email="u2@test.com", password="secret123")
    headers_u2 = api_headers(client)
    r = client.patch(f"/tasks/{tid}", json={"status": "doing"}, headers=headers_u2)
    assert r.status_code == 404


def test_tasks_write_requires_csrf(client):
    register(client, password="secret123")
    r = client.post("/tasks", json={"title": "x"}, content_type="application/json")
    assert r.status_code == 403
    assert "csrf" in r.get_json()["error"]
