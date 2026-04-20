from __future__ import annotations

from typing import Any, Dict, List

REQUIRED_TOP = {"scenario_number", "soap"}
REQUIRED_SOAP = {"subjective", "objective", "assessment", "plan"}


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def validate_prediction_structure(pred: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    if not isinstance(pred, dict):
        return {"valid": False, "errors": ["prediction is not a dict"]}

    missing_top = REQUIRED_TOP - set(pred.keys())
    if missing_top:
        errors.append(f"missing top-level keys: {sorted(missing_top)}")

    soap = pred.get("soap")
    if not isinstance(soap, dict):
        errors.append("soap must be a dict")
        return {"valid": False, "errors": errors}

    missing_soap = REQUIRED_SOAP - set(soap.keys())
    if missing_soap:
        errors.append(f"missing soap keys: {sorted(missing_soap)}")

    subj = soap.get("subjective", {})
    obj = soap.get("objective", {})

    if not isinstance(subj, dict):
        errors.append("subjective must be a dict")
    if not isinstance(obj, dict):
        errors.append("objective must be a dict")

    return {"valid": len(errors) == 0, "errors": errors}


def flatten_prediction(pred: Dict[str, Any]) -> List[Dict[str, str]]:
    facts: List[Dict[str, str]] = []
    soap = pred.get("soap", {}) or {}
    subj = soap.get("subjective", {}) or {}
    obj = soap.get("objective", {}) or {}

    def add(section: str, typ: str, text: str) -> None:
        if text is None:
            return
        text = str(text).strip()
        if not text:
            return
        facts.append({"section_pred": section, "type": typ, "content": text})

    add("subjective", "chief_complaint", subj.get("chief_complaint", ""))

    for x in _as_list(subj.get("history_of_present_illness")):
        add("subjective", "history_of_present_illness", x)
    for x in _as_list(subj.get("associated_symptoms")):
        add("subjective", "associated_symptom", x)
    for x in _as_list(subj.get("negatives")):
        add("subjective", "negative", x)
    for x in _as_list(subj.get("relevant_history")):
        add("subjective", "relevant_history", x)

    vitals = obj.get("vitals", {})
    if isinstance(vitals, dict):
        for k, v in vitals.items():
            add("objective", "vital_sign", f"{k}: {v}")

    for x in _as_list(obj.get("exam_findings")):
        add("objective", "exam_finding", x)
    for x in _as_list(obj.get("observed_general_state")):
        add("objective", "observed_state", x)

    for x in _as_list(soap.get("assessment")):
        add("assessment", "assessment", x)
    for x in _as_list(soap.get("plan")):
        add("plan", "plan", x)

    return facts
