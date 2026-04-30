from app.services.triage_classifier.severity_flagging import (
    normalize_text,
    find_matches,
    detect_presentations,
    apply_modifiers,
    check_hard_overrides,
    score_to_ats,
    build_severity_flag_notes,
    flag_high_severity,
)


def test_normalize_text_replaces_smart_punctuation():
    assert normalize_text("I’m “wheezy” — today") == "I'm \"wheezy\" - today"


def test_find_matches_ignores_negated_symptoms():
    matches = find_matches(
        "Patient denies chest pain. Later, the patient reports shortness of breath.",
        [r"\bchest pain\b", r"\bshortness of breath\b"],
    )

    lowered = [m.lower() for m in matches]

    assert "chest pain" not in lowered
    assert "shortness of breath" in lowered


def test_detect_presentations_finds_chest_pain():
    presentations = detect_presentations("Patient has chest pain.")

    assert "cardiac_chest_pain" in presentations
    assert presentations["cardiac_chest_pain"]["score"] == 4


def test_apply_modifiers_increases_score():
    presentations = detect_presentations("Patient has chest pain and is sweaty.")

    apply_modifiers("Patient has chest pain and is sweaty.", presentations)

    assert presentations["cardiac_chest_pain"]["score"] > 4
    assert "cardiac_features" in presentations["cardiac_chest_pain"]["upward_modifiers"]


def test_hard_override_detects_ongoing_seizure():
    overrides = check_hard_overrides("Patient has an ongoing seizure.")

    assert overrides[0]["ats"] == 1
    assert overrides[0]["name"] == "ats_1_seizure"


def test_score_to_ats_mapping():
    assert score_to_ats(6) == 1
    assert score_to_ats(4) == 2
    assert score_to_ats(3) == 3
    assert score_to_ats(2) == 4
    assert score_to_ats(1) == 5
    assert score_to_ats(0) is None


def test_build_notes_no_flags():
    assert build_severity_flag_notes(None, {}, []) == "No severity flags detected."


def test_flag_high_severity_chest_pain_rule():
    result = flag_high_severity("Patient has chest pain and is sweaty.")

    assert result["is_high_severity"] is True
    assert result["recommended_ats_category"] in {1, 2}
    assert "chest pain" in result["severity_flag_notes"].lower()


def test_flag_high_severity_no_flags():
    result = flag_high_severity("Patient has a mild sore finger.")

    assert result["is_high_severity"] is False
    assert result["recommended_ats_category"] is None