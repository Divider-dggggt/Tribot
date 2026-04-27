from datetime import datetime

from app.main import app
from app.core.security import get_current_user


def admin_user():
    return {
        "id": 1,
        "name": "Admin User",
        "email": "admin@test.com",
        "role": "admin",
        "deactivated_at": None,
        "password_changed_at": None,
        "created_at": datetime.now(),
    }


def clinician_user():
    return {
        "id": 2,
        "name": "Clinician User",
        "email": "clinician@test.com",
        "role": "clinician",
        "deactivated_at": None,
        "password_changed_at": None,
        "created_at": datetime.now(),
    }


def test_get_users_success(monkeypatch):
    monkeypatch.setattr("app.routers.users.db.get_active_users", lambda: [admin_user()])

    app.dependency_overrides[get_current_user] = admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.get("/users")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["role"] == "admin"


def test_get_user_not_found(monkeypatch):
    monkeypatch.setattr("app.routers.users.db.get_user_by_id", lambda user_id: None)

    app.dependency_overrides[get_current_user] = admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.get("/users/999")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_non_admin_cannot_get_users(client):
    response = client.get("/users")

    assert response.status_code == 403
    assert "Access restricted" in response.json()["detail"]


def test_deactivate_self_returns_400(monkeypatch):
    app.dependency_overrides[get_current_user] = admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.patch("/users/1/deactivate")

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Admin cannot deactivate their own account"