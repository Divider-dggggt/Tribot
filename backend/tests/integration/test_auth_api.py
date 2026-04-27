def test_login_success(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.authenticate_user", lambda email, password: {
        "id": 1,
        "email": email,
        "role": "clinician",
    })

    monkeypatch.setattr("app.routers.auth.create_access_token", lambda data: "fake-token")

    response = client.post("/login", json={
        "email": "clinician@test.com",
        "password": "password123"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "fake-token"
    assert data["token_type"] == "bearer"
    assert data["role"] == "clinician"


def test_login_invalid_credentials(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.authenticate_user", lambda email, password: None)

    response = client.post("/login", json={
        "email": "wrong@test.com",
        "password": "wrong"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_me_returns_current_user(client):
    response = client.get("/me")

    assert response.status_code == 200
    assert response.json()["role"] == "clinician"