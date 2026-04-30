from datetime import datetime


def test_get_cases_returns_open_cases(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.get_open_cases", lambda: [
        {
            "case_id": 1,
            "user_id": 1,
            "patient_name": "John Doe",
            "medicare_number": "12345678901",
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

    response = client.get("/cases")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["case_id"] == 1
    assert data[0]["ats_category"] == 2


def test_get_case_by_id_success(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.get_case_by_id", lambda case_id: {
        "case_id": case_id,
        "user_id": 1,
        "patient_name": "John Doe",
        "medicare_number": "12345678901",
        "case_dialogue": "Patient reports chest pain.",
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

    response = client.get("/cases/1")

    assert response.status_code == 200
    assert response.json()["case_id"] == 1


def test_get_case_by_id_not_found(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.get_case_by_id", lambda case_id: None)

    response = client.get("/cases/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"


def test_resolve_case_success(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.resolve_case", lambda case_id: {
        "case_id": case_id,
        "resolved_at": datetime.now(),
    })

    response = client.patch("/cases/1/resolve")

    assert response.status_code == 200
    assert response.json()["case_id"] == 1
    assert response.json()["resolved_at"] is not None


def test_resolve_case_not_found(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.resolve_case", lambda case_id: None)

    response = client.patch("/cases/999/resolve")

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"


def test_reopen_case_success(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.reopen_case", lambda case_id: {
        "case_id": case_id,
        "resolved_at": None,
    })

    response = client.patch("/cases/1/reopen")

    assert response.status_code == 200
    assert response.json()["case_id"] == 1
    assert response.json()["resolved_at"] is None


def test_override_ats_success(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.override_ats_classification", lambda case_id, override_ats, override_reason: {
        "case_id": case_id,
        "ats_category": override_ats,
        "ats_source": "override",
        "override_ats": override_ats,
        "override_reason": override_reason,
    })

    response = client.patch("/cases/1/ats", json={
        "override_ats": 1,
        "override_reason": "Clinician reviewed patient condition"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["ats_category"] == 1
    assert data["ats_source"] == "override"
    assert data["message"] == "ATS classification overridden successfully"


def test_override_ats_invalid_value_returns_422(client):
    response = client.patch("/cases/1/ats", json={
        "override_ats": 6,
        "override_reason": "Invalid value"
    })

    assert response.status_code == 422


def test_override_ats_case_not_found(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.override_ats_classification", lambda case_id, override_ats, override_reason: None)

    response = client.patch("/cases/999/ats", json={
        "override_ats": 2,
        "override_reason": "Valid but missing case"
    })

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"


def test_undo_ats_override_success(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.undo_ats_override", lambda case_id: {
        "case_id": case_id,
        "ats_category": 2,
        "ats_source": "rule",
        "override_ats": None,
        "override_reason": None,
    })

    response = client.patch("/cases/1/ats/undo")

    assert response.status_code == 200
    assert response.json()["ats_source"] == "rule"
    assert response.json()["override_ats"] is None
    assert response.json()["message"] == "ATS override removed successfully"


def test_undo_ats_override_when_not_overridden_returns_400(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.undo_ats_override", lambda case_id: {
        "error": "Case is not currently overridden"
    })

    response = client.patch("/cases/1/ats/undo")

    assert response.status_code == 400
    assert response.json()["detail"] == "Case is not currently overridden"


def test_generate_case_summary_success(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.get_case_by_id", lambda case_id: {
        "case_id": case_id,
        "case_dialogue": "Patient reports chest pain."
    })

    monkeypatch.setattr(
        "app.routers.cases.deidentify_dialogue",
        lambda text: {"deidentified_text": text}
    )

    monkeypatch.setattr(
        "app.routers.cases.generate_soap_summary",
        lambda text: {
            "soap_markdown": "## Subjective\nPatient reports chest pain.",
            "brief_summary": "Chest pain reported."
        }
    )

    monkeypatch.setattr(
        "app.routers.cases.db.upsert_clinical_summary",
        lambda case_id, soap_summary, brief_summary: {
            "case_id": case_id,
            "soap_summary": soap_summary,
            "brief_summary": brief_summary,
        }
    )

    response = client.post("/cases/1/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == 1
    assert data["brief_summary"] == "Chest pain reported."
    assert data["message"] == "Clinical summary generated successfully"


def test_generate_case_summary_case_not_found(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.get_case_by_id", lambda case_id: None)

    response = client.post("/cases/999/summary")

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"


def test_generate_case_summary_missing_dialogue(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.get_case_by_id", lambda case_id: {
        "case_id": case_id,
        "case_dialogue": ""
    })

    response = client.post("/cases/1/summary")

    assert response.status_code == 400
    assert response.json()["detail"] == "Case dialogue not found"


def test_generate_case_summary_failure_returns_500(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.get_case_by_id", lambda case_id: {
        "case_id": case_id,
        "case_dialogue": "Patient reports chest pain."
    })

    monkeypatch.setattr(
        "app.routers.cases.deidentify_dialogue",
        lambda text: {"deidentified_text": text}
    )

    def fake_generate_soap_summary(text):
        raise RuntimeError("summary failed")

    monkeypatch.setattr(
        "app.routers.cases.generate_soap_summary",
        fake_generate_soap_summary
    )

    response = client.post("/cases/1/summary")

    assert response.status_code == 500
    assert "Failed to generate summary" in response.json()["detail"]


def test_undo_ats_override_case_not_found(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.undo_ats_override", lambda case_id: None)

    response = client.patch("/cases/999/ats/undo")

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"


def test_undo_ats_override_no_restore_available_returns_400(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.undo_ats_override", lambda case_id: {
        "error": "No model or rule ATS available to restore"
    })

    response = client.patch("/cases/1/ats/undo")

    assert response.status_code == 400
    assert response.json()["detail"] == "No model or rule ATS available to restore"


def test_get_resolved_cases(client, monkeypatch):
    from datetime import datetime

    monkeypatch.setattr("app.routers.cases.db.get_resolved_cases", lambda: [
        {
            "case_id": 20,
            "user_id": 1,
            "patient_name": "Resolved Patient",
            "medicare_number": "12345678901",
            "severity_flagged": False,
            "created_at": datetime.now(),
            "resolved_at": datetime.now(),
            "ats_category": 4,
            "ats_source": "model",
            "override_ats": None,
            "override_reason": None,
            "age": None,
            "gender": None,
        }
    ])

    response = client.get("/cases?resolved=true")

    assert response.status_code == 200
    assert response.json()[0]["resolved_at"] is not None


def test_generate_summary_fast_response_returns_placeholder(client, monkeypatch):
    monkeypatch.setattr("app.routers.cases.db.get_case_by_id", lambda case_id: {
        "case_id": case_id,
        "case_dialogue": "Patient reports chest pain.",
    })

    monkeypatch.setattr("app.routers.cases.deidentify_dialogue", lambda text: {"deidentified_text": text})
    monkeypatch.setattr("app.routers.cases.db.upsert_clinical_summary", lambda **kwargs: {
        "case_id": kwargs["case_id"],
        "soap_summary": kwargs["soap_summary"],
        "brief_summary": kwargs["brief_summary"],
    })

    response = client.post("/cases/1/summary?fast_response=true")

    assert response.status_code == 200
    data = response.json()
    assert data["soap_summary"] == "Generating clinical summary..."
    assert data["brief_summary"] == "Generating brief summary..."
    assert data["message"] == "Clinical summary generation started"