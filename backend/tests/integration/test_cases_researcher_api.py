from datetime import datetime

from app.main import app
from app.core.security import get_current_user


def researcher_user():
    return {
        "id": 3,
        "name": "Researcher User",
        "email": "researcher@test.com",
        "role": "researcher",
        "deactivated_at": None,
        "password_changed_at": None,
        "created_at": datetime.now(),
    }


def test_researcher_get_case_anonymises_identity(monkeypatch):
    app.dependency_overrides[get_current_user] = researcher_user

    monkeypatch.setattr("app.routers.cases.db.get_case_by_id", lambda case_id: {
        "case_id": case_id,
        "user_id": 1,
        "patient_name": "John Smith",
        "medicare_number": "12345678901",
        "case_dialogue": "This is John Smith. Patient reports chest pain.",
        "severity_flagged": True,
        "created_at": datetime.now(),
        "resolved_at": None,
        "ats_category": 2,
        "ats_source": "rule",
        "override_ats": None,
        "override_reason": None,
        "age": 45,
        "gender": "male",
        "pred_ats": 3,
        "pred_confidence": 0.91,
        "model_used": "deberta",
        "flag_ats": 2,
        "flag_notes": "Chest pain detected",
        "soap_summary": "SOAP summary",
        "brief_summary": "Brief summary",
    })

    monkeypatch.setattr(
        "app.routers.cases.deidentify_dialogue",
        lambda text: {"deidentified_text": "This is [PATIENT_NAME]. Patient reports chest pain."}
    )

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.get("/cases/1")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["patient_name"] == "[REDACTED]"
    assert data["medicare_number"] == "[REDACTED]"
    assert "[PATIENT_NAME]" in data["case_dialogue"]


def test_researcher_get_cases_anonymises_list(monkeypatch):
    app.dependency_overrides[get_current_user] = researcher_user

    from datetime import datetime

    monkeypatch.setattr("app.routers.cases.db.get_open_cases", lambda: [
        {
            "case_id": 1,
            "user_id": 1,
            "patient_name": "John Smith",
            "medicare_number": "12345678901",
            "case_dialogue": "This is John Smith.",
            "severity_flagged": True,
            "created_at": datetime.now(),
            "resolved_at": None,
            "ats_category": 2,
            "ats_source": "rule",
            "override_ats": None,
            "override_reason": None,
            "age": 45,
            "gender": "male",
        }
    ])

    monkeypatch.setattr(
        "app.routers.cases.deidentify_dialogue",
        lambda text: {"deidentified_text": "This is [PATIENT_NAME]."}
    )

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        response = test_client.get("/cases")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data[0]["patient_name"] == "[REDACTED]"
    assert data[0]["medicare_number"] == "[REDACTED]"
    assert data[0]["case_dialogue"] == "This is [PATIENT_NAME]."