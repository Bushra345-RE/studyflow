import pytest

from app import create_app, db
from config import TestConfig


class NoCsrfConfig(TestConfig):
    CSRF_ENABLED = False


@pytest.fixture
def app():
    app = create_app(NoCsrfConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def register(client, username="alice", password="password123"):
    return client.post("/register", data={"username": username, "password": password},
                       follow_redirects=True)


@pytest.fixture
def auth_client(client):
    register(client)
    return client
