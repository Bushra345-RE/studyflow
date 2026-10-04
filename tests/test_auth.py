from app import create_app
from config import TestConfig
from tests.conftest import register


def test_register_login_logout_flow(client):
    assert b"Dashboard" in register(client).data
    client.post("/logout")
    assert client.get("/dashboard").status_code == 302
    resp = client.post("/login", data={"username": "alice", "password": "password123"},
                       follow_redirects=True)
    assert b"Dashboard" in resp.data


def test_wrong_password_rejected(client):
    register(client)
    client.post("/logout")
    resp = client.post("/login", data={"username": "alice", "password": "wrongpass1"})
    assert b"Invalid username or password" in resp.data


def test_duplicate_and_weak_registration(client):
    register(client)
    client.post("/logout")
    assert b"already taken" in register(client).data
    assert b"at least 8" in register(client, "bob", "short").data
    assert b"3-32" in register(client, "a!", "password123").data


def test_password_is_hashed(app, client):
    from app.models import User
    register(client)
    assert User.query.first().password_hash != "password123"


def test_csrf_enforced_when_enabled():
    app = create_app(TestConfig)  # CSRF on
    client = app.test_client()
    assert client.post("/login", data={"username": "a", "password": "b"}).status_code == 400
    client.get("/login")
    with client.session_transaction() as sess:
        token = sess["_csrf"]
    resp = client.post("/login", data={"username": "a", "password": "b", "csrf_token": token})
    assert resp.status_code == 200  # token accepted; login itself fails with a flash
