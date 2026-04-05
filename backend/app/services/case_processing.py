from app.services.triage_classifier.severity_flagging import flag_high_severity


def soap_summary(text: str) -> str:
    soap = {
        "subjective": "Patient reports severe chest pain that began approximately one hour ago and radiates to the left arm and jaw. Patient also reports severe shortness of breath and dizziness",
        "objective": {
            "heart_rate": "elevated",
            "blood_pressure": "120/80",
            "respiratory_rate": "22",
            "oxygen_saturation": "95%",
            "notes": "Patient appears distressed and short of breath. Speech slightly slurred. Visible bleeding from left forearm wound. Patient appears pale.",
        },
        "assessment": "Symptoms indicate potential acute coronary syndrome and possible neurological involvement. Heavy bleeding also observed. Patient classified as ATS Category 2 due to multiple high-risk symptoms.",
        "plan": "Immediate ECG and cardiac monitoring.",
    }

    return f"""
    S - Subjective
    {soap['subjective']}

    O - Objective
    Heart rate: {soap['objective']['heart_rate']}
    Blood pressure: {soap['objective']['blood_pressure']}
    Respiratory rate: {soap['objective']['respiratory_rate']}
    Oxygen saturation: {soap['objective']['oxygen_saturation']}
    Notes: {soap['objective']['notes']}

    A - Assessment
    {soap['assessment']}

    P - Plan
    {soap['plan']}
    """.strip()


def triage_classification(text: str) -> str:
    return "triage classification call..."


def classification_algo(text: str) -> dict:
    severity_info = flag_high_severity(text)
    triage_classification(text)

    return {
        "model_name": "baseline_model",
        "ats_category": 2,
        "confidence_score": 0.85,
        "severity_flags": severity_info,
        "matched_categories": {
            "chest_pain": 2,
        },
        "flags": {
            "chest_pain": ["severe chest pain", "pain radiating to left arm"],
            "shortness_of_breath": ["severe shortness of breath"],
            "stroke_symptoms": ["slurred speech", "weakness on right side"],
            "severe_bleeding": ["bleeding heavily"],
        },
    }
