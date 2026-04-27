from datetime import datetime


def test_create_case_success(client, monkeypatch):
    def fake_classify_triage(case_dialogue):
        return {
            "ats_category": 2,
            "model_confidence": 0.95,
            "is_high_severity": True,
            "severity_flag_notes": "Shortness of breath detected",
            "decision_source": "rule",
            "model_ats_category": 3,
        }

    def fake_deidentify_dialogue(case_dialogue):
        return {"deidentified_text": case_dialogue}

    def fake_has_open_case_for_medicare(medicare_number):
        return False

    def fake_add_case(**kwargs):
        return {
            "case_id": 1,
            "patient_name": kwargs["patient_name"],
            "medicare_number": kwargs["medicare_number"],
            "case_dialogue": kwargs["case_dialogue"],
            "severity_flagged": kwargs["severity_flagged"],
            "created_at": datetime.now(),
            "resolved_at": None,
            "ats_category": kwargs["ats_category"],
            "ats_source": kwargs["ats_source"],
            "override_ats": None,
            "override_reason": None,
            "age": kwargs["age"],
            "gender": kwargs["gender"],
        }

    monkeypatch.setattr("app.routers.cases.classify_triage", fake_classify_triage)
    monkeypatch.setattr("app.routers.cases.deidentify_dialogue", fake_deidentify_dialogue)
    monkeypatch.setattr("app.routers.cases.db.has_open_case_for_medicare", fake_has_open_case_for_medicare)
    monkeypatch.setattr("app.routers.cases.db.add_case", fake_add_case)
    monkeypatch.setattr("app.routers.cases.db.add_model_prediction", lambda **kwargs: None)
    monkeypatch.setattr("app.routers.cases.db.add_severity_flag", lambda **kwargs: None)
    monkeypatch.setattr("app.routers.cases.db.upsert_clinical_summary", lambda **kwargs: None)

    response = client.post("/cases?fast_response=true", json={
        "patient_name": "John Doe",
        "medicare_number": "12345678901",
        "case_dialogue": "I feel short of breath.",
        "age": 45,
        "gender": "male",
    })

    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == 1
    assert data["patient_name"] == "John Doe"
    assert data["medicare_number"] == "12345678901"
    assert data["severity_flagged"] is True
    assert data["ats_category"] == 2
    assert data["ats_source"] == "rule"
    assert data["pred_ats"] == 3
    assert data["pred_confidence"] == 0.95
    assert data["flag_notes"] == "Shortness of breath detected"


def test_create_case_missing_dialogue_returns_422(client):
    response = client.post("/cases", json={
        "patient_name": "John Doe",
        "medicare_number": "12345678901",
        "age": 45,
        "gender": "male",
    })

    assert response.status_code == 422


def test_create_case_invalid_medicare_returns_422(client):
    response = client.post("/cases", json={
        "patient_name": "John Doe",
        "medicare_number": "abc",
        "case_dialogue": "Patient has chest pain.",
        "age": 45,
        "gender": "male",
    })

    assert response.status_code == 422


def test_create_case_invalid_gender_returns_422(client):
    response = client.post("/cases", json={
        "patient_name": "John Doe",
        "medicare_number": "12345678901",
        "case_dialogue": "Patient has chest pain.",
        "age": 45,
        "gender": "unknown",
    })

    assert response.status_code == 422


def test_create_case_allows_missing_age_and_gender(client, monkeypatch):
    def fake_classify_triage(case_dialogue):
        return {
            "ats_category": 3,
            "model_confidence": 0.88,
            "is_high_severity": False,
            "severity_flag_notes": "",
            "decision_source": "model",
            "model_ats_category": 3,
        }

    def fake_deidentify_dialogue(case_dialogue):
        return {"deidentified_text": case_dialogue}

    def fake_add_case(**kwargs):
        from datetime import datetime
        return {
            "case_id": 2,
            "patient_name": kwargs["patient_name"],
            "medicare_number": kwargs["medicare_number"],
            "case_dialogue": kwargs["case_dialogue"],
            "severity_flagged": kwargs["severity_flagged"],
            "created_at": datetime.now(),
            "resolved_at": None,
            "ats_category": kwargs["ats_category"],
            "ats_source": kwargs["ats_source"],
            "override_ats": None,
            "override_reason": None,
            "age": kwargs["age"],
            "gender": kwargs["gender"],
        }

    monkeypatch.setattr("app.routers.cases.classify_triage", fake_classify_triage)
    monkeypatch.setattr("app.routers.cases.deidentify_dialogue", fake_deidentify_dialogue)
    monkeypatch.setattr("app.routers.cases.db.has_open_case_for_medicare", lambda medicare_number: False)
    monkeypatch.setattr("app.routers.cases.db.add_case", fake_add_case)
    monkeypatch.setattr("app.routers.cases.db.add_model_prediction", lambda **kwargs: None)
    monkeypatch.setattr("app.routers.cases.db.add_severity_flag", lambda **kwargs: None)
    monkeypatch.setattr("app.routers.cases.db.upsert_clinical_summary", lambda **kwargs: None)

    response = client.post("/cases?fast_response=true", json={
        "patient_name": "Jane Doe",
        "medicare_number": "12345678901",
        "case_dialogue": "Patient has mild abdominal pain."
    })

    assert response.status_code == 200
    data = response.json()
    assert data["age"] is None
    assert data["gender"] is None
    assert data["ats_category"] == 3
    assert data["ats_source"] == "model"


def test_create_case_duplicate_medicare_returns_409(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.cases.db.has_open_case_for_medicare",
        lambda medicare_number: True,
    )

    response = client.post("/cases", json={
        "patient_name": "John Doe",
        "medicare_number": "12345678901",
        "case_dialogue": "Patient reports chest pain.",
        "age": 45,
        "gender": "male",
    })

    assert response.status_code == 409