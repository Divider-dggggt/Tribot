import pytest

from app.services.anonymisation import deidentify_dialogue, CONFIG


def test_deidentify_replaces_email_phone_address_id_time_and_name():
    text = (
        "Nurse: This is John Smith. "
        "Contact john@example.com or 0412 345 678. "
        "Lives at 12 King Street. "
        "Medicare 12345678901. "
        "Arrived at 10:30am."
    )

    result = deidentify_dialogue(text)

    assert result["deidentification_applied"] is True
    assert "[PATIENT_NAME]" in result["deidentified_text"]
    assert "[EMAIL]" in result["deidentified_text"]
    assert "[PHONE]" in result["deidentified_text"]
    assert "[ADDRESS]" in result["deidentified_text"]
    assert "[ID_NUMBER]" in result["deidentified_text"]
    assert "[TIME]" in result["deidentified_text"]


def test_deidentify_keeps_age_and_date_by_default():
    text = "Patient is 45 years old. DOB 01/02/1980."

    result = deidentify_dialogue(text)

    assert "45 years old" in result["deidentified_text"]
    assert "01/02/1980" in result["deidentified_text"]


def test_deidentify_raises_type_error_for_non_string():
    with pytest.raises(TypeError):
        deidentify_dialogue(123)


def test_deidentify_can_mask_age_and_date_when_enabled(monkeypatch):
    monkeypatch.setitem(CONFIG, "mask_age", True)
    monkeypatch.setitem(CONFIG, "mask_date", True)
    monkeypatch.setitem(CONFIG, "mask_dob", True)

    result = deidentify_dialogue("DOB 01/02/1980. Patient is 45 years old.")

    assert "[DOB]" in result["deidentified_text"] or "[DATE]" in result["deidentified_text"]
    assert "[AGE]" in result["deidentified_text"]