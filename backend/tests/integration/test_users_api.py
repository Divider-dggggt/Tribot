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


def test_get_all_users_success(monkeypatch):
    monkeypatch.setattr("app.routers.users.db.get_all_users", lambda: [admin_user(), clinician_user()])

    app.dependency_overrides[get_current_user] = admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.get("/users/all")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_deactivated_users_success(monkeypatch):
    deactivated = clinician_user()
    deactivated["deactivated_at"] = datetime.now()

    monkeypatch.setattr("app.routers.users.db.get_deactivated_users", lambda: [deactivated])

    app.dependency_overrides[get_current_user] = admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.get("/users/deactivated")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["deactivated_at"] is not None


def test_create_user_success(monkeypatch):
    new_user = {
        "id": 4,
        "name": "New User",
        "email": "new@test.com",
        "role": "clinician",
        "deactivated_at": None,
        "password_changed_at": None,
        "created_at": datetime.now(),
    }

    monkeypatch.setattr("app.routers.users.pwd_context.hash", lambda password: "hashed-password")
    monkeypatch.setattr("app.routers.users.db.create_user", lambda **kwargs: new_user)

    app.dependency_overrides[get_current_user] = admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.post("/users", json={
            "name": "New User",
            "email": "new@test.com",
            "password": "password123",
            "role": "clinician",
        })

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["email"] == "new@test.com"


def test_update_own_account_success(monkeypatch):
    monkeypatch.setattr("app.routers.users.db.get_user_by_id", lambda user_id: clinician_user())

    updated = clinician_user()
    updated["name"] = "Updated Clinician"

    monkeypatch.setattr("app.routers.users.db.update_user", lambda *args, **kwargs: updated)

    app.dependency_overrides[get_current_user] = clinician_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.put("/users/2", json={
            "name": "Updated Clinician",
            "email": "clinician@test.com",
            "role": None,
            "password": None,
            "old_password": None,
        })

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Clinician"


def test_non_admin_cannot_update_another_user(monkeypatch):
    monkeypatch.setattr("app.routers.users.db.get_user_by_id", lambda user_id: admin_user())

    app.dependency_overrides[get_current_user] = clinician_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.put("/users/1", json={
            "name": "Hack Attempt",
            "email": "admin@test.com",
            "role": None,
            "password": None,
            "old_password": None,
        })

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "You can only update your own account"


def test_non_admin_cannot_change_role(monkeypatch):
    monkeypatch.setattr("app.routers.users.db.get_user_by_id", lambda user_id: clinician_user())

    app.dependency_overrides[get_current_user] = clinician_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.put("/users/2", json={
            "name": "Clinician User",
            "email": "clinician@test.com",
            "role": "admin",
            "password": None,
            "old_password": None,
        })

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Only admins can change roles"


def test_deactivate_user_success(monkeypatch):
    deactivated = clinician_user()
    deactivated["deactivated_at"] = datetime.now()

    monkeypatch.setattr("app.routers.users.db.deactivate_user", lambda user_id: deactivated)

    app.dependency_overrides[get_current_user] = admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.patch("/users/2/deactivate")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["deactivated_at"] is not None


def test_reactivate_user_success(monkeypatch):
    reactivated = clinician_user()
    reactivated["deactivated_at"] = None

    monkeypatch.setattr("app.routers.users.db.reactivate_user", lambda user_id: reactivated)

    app.dependency_overrides[get_current_user] = admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.patch("/users/2/reactivate")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["deactivated_at"] is None


def test_update_user_not_found(monkeypatch):
    monkeypatch.setattr("app.routers.users.db.get_user_by_id", lambda user_id: None)

    app.dependency_overrides[get_current_user] = admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.put("/users/999", json={
            "name": "Missing User",
            "email": "missing@test.com",
            "role": None,
            "password": None,
            "old_password": None,
        })

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_password_requires_old_password_for_non_admin(monkeypatch):
    monkeypatch.setattr("app.routers.users.db.get_user_by_id", lambda user_id: clinician_user())

    app.dependency_overrides[get_current_user] = clinician_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.put("/users/2", json={
            "name": "Clinician User",
            "email": "clinician@test.com",
            "role": None,
            "password": "new-password",
            "old_password": None,
        })

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Old password is required to change password"


def test_update_password_rejects_wrong_old_password(monkeypatch):
    auth_user = clinician_user()
    auth_user["password"] = "hashed-old-password"

    monkeypatch.setattr("app.routers.users.db.get_user_by_id", lambda user_id: clinician_user())
    monkeypatch.setattr("app.routers.users.db.get_user_by_email", lambda email: auth_user)
    monkeypatch.setattr("app.routers.users.pwd_context.verify", lambda plain, hashed: False)

    app.dependency_overrides[get_current_user] = clinician_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.put("/users/2", json={
            "name": "Clinician User",
            "email": "clinician@test.com",
            "role": None,
            "password": "new-password",
            "old_password": "wrong-password",
        })

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Old password is incorrect"


def test_deactivate_user_not_found(monkeypatch):
    monkeypatch.setattr("app.routers.users.db.deactivate_user", lambda user_id: None)

    app.dependency_overrides[get_current_user] = admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.patch("/users/999/deactivate")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found or already deactivated"


def test_reactivate_user_not_found(monkeypatch):
    monkeypatch.setattr("app.routers.users.db.reactivate_user", lambda user_id: None)

    app.dependency_overrides[get_current_user] = admin_user

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.patch("/users/999/reactivate")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found or not deactivated"