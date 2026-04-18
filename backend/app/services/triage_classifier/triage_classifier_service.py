from typing import Any, Dict
import sys
import json
from pathlib import Path

# from .baseline_predict import predict_ats
from .sprint2_deberta_classifier import predict_ats
# from .sprint2_setfit_classifier import predict_ats

from .severity_flagging import flag_high_severity


def classify_triage(dialogue_text: str) -> Dict[str, Any]:
    """
    Classify a triage dialogue using:
    1. Rule-based severity flagging first
    2. Baseline model inference if no high-severity rule is matched

    Args:
        dialogue_text: Raw dialogue text between clinician and patient.

    Returns:
        {
            "ats_category": int,
            "model_confidence": float,
            "is_high_severity": bool,
            "flags_detected": dict[str, list[str]],
            "decision_source": str,
            "rule_based_ats_category": int | None,
            "model_ats_category": int
        }
    """
    if not isinstance(dialogue_text, str) or not dialogue_text.strip():
        raise ValueError("Input dialogue_text cannot be empty.")

    cleaned_text = dialogue_text.strip()

    # get results from rule-based service and classification model
    severity_result = flag_high_severity(cleaned_text)
    model_result = predict_ats(cleaned_text)

    is_high_severity = severity_result.get("is_high_severity", False)
    rule_based_ats_category = severity_result.get("recommended_ats_category")
    model_ats_category = model_result["ats_category"]
    model_confidence = model_result["confidence"]
    # flags_detected = severity_result.get("flags", {})
    severity_flag_notes = severity_result.get("severity_flag_notes")

    if is_high_severity and rule_based_ats_category is not None:
        if (rule_based_ats_category) <= int(model_ats_category):
            final_ats_category = int(rule_based_ats_category)
            decision_source = "rule"
        else:
            final_ats_category = int(model_ats_category)
            decision_source = "model"
    else:
        final_ats_category = int(model_ats_category)
        decision_source = "model"

    return {
        "ats_category": final_ats_category,
        "model_confidence": model_confidence,
        "is_high_severity": is_high_severity,
        "severity_flag_notes": severity_flag_notes,
        "decision_source": decision_source,
        "rule_based_ats_category": rule_based_ats_category,
        "model_ats_category": model_ats_category,
    }

def read_input_text() -> str:
    """
    Read from a file path argument if provided, otherwise from stdin.
    """
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")
        return input_path.read_text(encoding="utf-8")

    if not sys.stdin.isatty():
        return sys.stdin.read()

    raise ValueError(
        "No input provided. Use either:\n"
        "  python severity_flagging.py path/to/file.txt\n"
        "or:\n"
        "  python severity_flagging.py < path/to/file.txt"
    )


def main():
    try:
        input_text = read_input_text()
        if not input_text.strip():
            raise ValueError("Input text is empty.")

        result = classify_triage(input_text)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()