import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture()
def app():
    """A Flask app instance configured for testing: in-memory SQLite,
    debug off, no rate limiting friction."""
    from app import create_app
    from config import Config

    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        RATELIMIT_ENABLED = False

    flask_app = create_app(TestConfig)
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client):
    """Issues a real JWT via the actual /api/auth/token endpoint and
    returns ready-to-use headers, so tests exercise the real auth path
    rather than bypassing it."""
    resp = client.post("/api/auth/token", json={"client_id": "pytest"})
    token = resp.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}
