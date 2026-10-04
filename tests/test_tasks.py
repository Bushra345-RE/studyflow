from datetime import date, timedelta

from tests.conftest import register


def add_task(client, **overrides):
    data = {"title": "Study Flask", "difficulty": 3, "est_minutes": 60}
    data.update(overrides)
    return client.post("/tasks/new", data=data, follow_redirects=True)


def test_dashboard_requires_login(client):
    assert client.get("/dashboard").status_code == 302
    assert client.get("/tasks").status_code == 302


def test_create_edit_toggle_delete_task(auth_client):
    assert b"Task created" in add_task(auth_client).data
    assert b"Study Flask" in auth_client.get("/tasks").data

    resp = auth_client.post("/tasks/1/edit", data={"title": "Study Django", "difficulty": 4,
                                                   "est_minutes": 90}, follow_redirects=True)
    assert b"Study Django" in resp.data

    auth_client.post("/tasks/1/toggle")
    assert b"Undo" in auth_client.get("/tasks").data

    assert b"Task deleted" in auth_client.post("/tasks/1/delete", follow_redirects=True).data
    assert b"No tasks found" in auth_client.get("/tasks").data


def test_invalid_task_returns_400_with_errors(auth_client):
    resp = add_task(auth_client, title="", difficulty=10)
    assert resp.status_code == 400 and b"Title is required" in resp.data


def test_users_cannot_touch_each_others_tasks(client):
    register(client, "alice")
    add_task(client)
    client.post("/logout")
    register(client, "bob")
    assert client.get("/tasks/1/edit").status_code == 404
    assert client.post("/tasks/1/delete").status_code == 404
    assert client.post("/tasks/1/toggle").status_code == 404


def test_subjects_and_filtering(auth_client):
    auth_client.post("/subjects", data={"name": "Python"})
    assert b"already have" in auth_client.post("/subjects", data={"name": "Python"},
                                               follow_redirects=True).data
    add_task(auth_client, subject_id=1, title="Python task")
    add_task(auth_client, title="General task")
    page = auth_client.get("/tasks?subject=1").data
    assert b"Python task" in page and b"General task" not in page


def test_deleting_subject_keeps_tasks(auth_client):
    auth_client.post("/subjects", data={"name": "Maths"})
    add_task(auth_client, subject_id=1)
    auth_client.post("/subjects/1/delete")
    assert b"Study Flask" in auth_client.get("/tasks").data


def test_dashboard_shows_overdue_count(auth_client):
    add_task(auth_client, due_date=(date.today() - timedelta(days=3)).isoformat())
    page = auth_client.get("/dashboard").data
    assert b"Overdue" in page and b"Focus list" in page


def test_404_page(auth_client):
    assert auth_client.get("/nope").status_code == 404
