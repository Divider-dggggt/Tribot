from datetime import datetime
from fastapi import HTTPException
import pytest

from app.core.security import authenticate_user, create_access_token, role_required


def test_authenticate_user_returns_none_when_user_missing(monkeypatch):
    monkeypatch.setattr("app.core.security.db.get_user_by_email", lambda email: None)

    assert authenticate_user("missing@test.com", "password") is None


def test_authenticate_user_returns_none_when_deactivated(monkeypatch):
    monkeypatch.setattr("app.core.security.db.get_user_by_email", lambda email: {
        "id": 1,
        "email": email,
        "password": "hashed",
        "role": "clinician",
        "deactivated_at": datetime.now(),
    })

    assert authenticate_user("test@test.com", "password") is None


def test_create_access_token_contains_token():
    token = create_access_token({"user_id": 1, "role": "clinician"})

    assert isinstance(token, str)
    assert len(token) > 0


def test_role_required_allows_correct_role():
    dependency = role_required("clinician")
    user = {"role": "clinician"}

    assert dependency(user) == user


def test_role_required_rejects_wrong_role():
    dependency = role_required("clinician")

    with pytest.raises(HTTPException) as exc:
        dependency({"role": "researcher"})

    assert exc.value.status_code == 403