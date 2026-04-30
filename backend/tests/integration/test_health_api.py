from app.main import app
from app.core.security import get_current_user


def test_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_health_success(monkeypatch):
    def fake_admin_user():
        return {
            "id": 1,
            "email": "admin@test.com",
            "role": "admin",
            "deactivated_at": None,
        }

    class FakeCursor:
        def execute(self, query):
            pass

        def fetchone(self):
            return (1,)

        def close(self):
            pass

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr("app.routers.health.get_connection", lambda: FakeConnection())

    app.dependency_overrides[get_current_user] = fake_admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.get("/health")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["routes_loaded"].startswith("ok")


def test_health_database_error(monkeypatch):
    def fake_admin_user():
        return {
            "id": 1,
            "email": "admin@test.com",
            "role": "admin",
            "deactivated_at": None,
        }

    def fake_get_connection():
        raise Exception("database unavailable")

    monkeypatch.setattr("app.routers.health.get_connection", fake_get_connection)

    app.dependency_overrides[get_current_user] = fake_admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.get("/health")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["database"] == "error"