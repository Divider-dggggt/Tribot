import pytest

from app.services.triage_classifier.triage_classifier_service import classify_triage


def test_classify_triage_raises_for_empty_input():
    with pytest.raises(ValueError):
        classify_triage("")


def test_classify_triage_uses_rule_when_rule_ats_lower(monkeypatch):
    monkeypatch.setattr(
        "app.services.triage_classifier.triage_classifier_service.flag_high_severity",
        lambda text: {
            "is_high_severity": True,
            "recommended_ats_category": 2,
            "severity_flag_notes": "ATS 2 | chest pain",
        },
    )

    monkeypatch.setattr(
        "app.services.triage_classifier.triage_classifier_service.predict_ats",
        lambda text: {
            "ats_category": 3,
            "confidence": 0.8,
        },
    )

    result = classify_triage("Patient has chest pain.")

    assert result["ats_category"] == 2
    assert result["decision_source"] == "rule"
    assert result["rule_based_ats_category"] == 2
    assert result["model_ats_category"] == 3


def test_classify_triage_uses_model_when_model_ats_lower(monkeypatch):
    monkeypatch.setattr(
        "app.services.triage_classifier.triage_classifier_service.flag_high_severity",
        lambda text: {
            "is_high_severity": True,
            "recommended_ats_category": 3,
            "severity_flag_notes": "ATS 3 | fever",
        },
    )

    monkeypatch.setattr(
        "app.services.triage_classifier.triage_classifier_service.predict_ats",
        lambda text: {
            "ats_category": 2,
            "confidence": 0.9,
        },
    )

    result = classify_triage("Patient has fever.")

    assert result["ats_category"] == 2
    assert result["decision_source"] == "model"


def test_classify_triage_uses_model_when_no_high_severity(monkeypatch):
    monkeypatch.setattr(
        "app.services.triage_classifier.triage_classifier_service.flag_high_severity",
        lambda text: {
            "is_high_severity": False,
            "recommended_ats_category": None,
            "severity_flag_notes": "No severity flags detected.",
        },
    )

    monkeypatch.setattr(
        "app.services.triage_classifier.triage_classifier_service.predict_ats",
        lambda text: {
            "ats_category": 4,
            "confidence": 0.7,
        },
    )

    result = classify_triage("Patient has mild symptoms.")

    assert result["ats_category"] == 4
    assert result["decision_source"] == "model"
    assert result["is_high_severity"] is False