from __future__ import annotations

from pathlib import Path
from typing import Dict
import sys
import json


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "final_model"

_MODEL = None


def _load_model() -> object:
    global _MODEL

    if _MODEL is not None:
        return _MODEL

    if not MODEL_DIR.exists():
        raise FileNotFoundError(f"Model directory not found: {MODEL_DIR}")

    try:
        from setfit import SetFitModel
    except ImportError as exc:
        raise ImportError(
            "Missing dependency for SetFit inference. Install `setfit`."
        ) from exc

    _MODEL = SetFitModel.from_pretrained(str(MODEL_DIR), local_files_only=True)
    return _MODEL


def _to_ats_category(pred_label: object) -> int:
    """
    Map model label to ATS category.
    SetFit head classes are often 0..4 for 5-class ATS, so convert to 1..5.
    """
    try:
        value = int(pred_label)
    except (TypeError, ValueError):
        raise ValueError(f"Unexpected predicted label: {pred_label}")

    if 0 <= value <= 4:
        return value + 1
    return value


def classify_triage(text: str) -> Dict[str, float | int]:
    """
    SetFit ATS classification interface.

    Args:
        text: Free-text triage input.

    Returns:
        {
            "ats_category": int,
            "confidence_score": float  # 0.0 ~ 1.0
        }
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Input text cannot be empty.")

    model = _load_model()
    cleaned_text = text.strip()

    pred_label = model.predict([cleaned_text])[0]

    if not hasattr(model, "predict_proba"):
        raise RuntimeError("Loaded SetFit model does not support `predict_proba`.")

    probs = model.predict_proba([cleaned_text])[0]

    try:
        import numpy as np

        pred_index = int(np.argmax(probs))
        confidence = float(probs[pred_index])
    except Exception:
        confidence = float(max(probs))

    ats_category = _to_ats_category(pred_label)

    return {
        "ats_category": ats_category,
        "confidence_score": round(confidence, 4),
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
