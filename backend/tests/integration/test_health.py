def test_app_starts(client):
    response = client.get("/docs")  # FastAPI always has this
    assert response.status_code == 200