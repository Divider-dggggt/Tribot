import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user

from datetime import datetime


@pytest.fixture
def fake_clinician_user():
    return {
        "id": 1,
        "name": "Test Clinician",
        "email": "clinician@test.com",
        "role": "clinician",
        "deactivated_at": None,
        "password_changed_at": None,
        "created_at": datetime.now(),
    }


@pytest.fixture
def client(fake_clinician_user):
    def override_get_current_user():
        return fake_clinician_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()