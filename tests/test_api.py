from tests.conftest import register


def test_api_requires_authentication(client):
    resp = client.get("/api/tasks")
    assert resp.status_code == 401 and resp.get_json()["error"]


def test_api_crud_cycle(auth_client):
    created = auth_client.post("/api/tasks", json={"title": "API task", "difficulty": 5,
                                                   "est_minutes": 120})
    assert created.status_code == 201
    body = created.get_json()
    assert body["priority"] in {"Low", "Medium", "High"} and body["id"] == 1

    assert auth_client.get("/api/tasks/1").get_json()["title"] == "API task"

    updated = auth_client.put("/api/tasks/1", json={"title": "Renamed", "done": True})
    assert updated.status_code == 200
    assert updated.get_json()["title"] == "Renamed" and updated.get_json()["done"] is True

    assert auth_client.delete("/api/tasks/1").status_code == 204
    assert auth_client.get("/api/tasks/1").status_code == 404


def test_api_validation_errors(auth_client):
    resp = auth_client.post("/api/tasks", json={"title": "", "difficulty": 99})
    assert resp.status_code == 422 and len(resp.get_json()["errors"]) >= 2


def test_api_rejects_non_json_body(auth_client):
    assert auth_client.post("/api/tasks", data="title=x").status_code == 400


def test_api_isolation_between_users(client):
    register(client, "alice")
    client.post("/api/tasks", json={"title": "secret"})
    client.post("/logout")
    register(client, "bob")
    assert client.get("/api/tasks").get_json() == []
    assert client.get("/api/tasks/1").status_code == 404
    assert client.delete("/api/tasks/1").status_code == 404


def test_api_priority_sort_and_stats(auth_client):
    auth_client.post("/api/tasks", json={"title": "later", "due_date": "2099-01-01"})
    auth_client.post("/api/tasks", json={"title": "overdue", "due_date": "2000-01-01"})
    ordered = auth_client.get("/api/tasks?sort=priority").get_json()
    assert ordered[0]["title"] == "overdue"
    stats = auth_client.get("/api/stats").get_json()
    assert stats["total"] == 2 and stats["overdue"] == 1
