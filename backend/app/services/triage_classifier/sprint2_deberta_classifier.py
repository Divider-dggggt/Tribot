from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple
import sys
import json

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "best_model"

_MODEL = None
_TOKENIZER = None
_DEVICE = None


def _load_model_and_tokenizer() -> Tuple[object, object, object]:
    global _MODEL, _TOKENIZER, _DEVICE

    if _MODEL is not None and _TOKENIZER is not None and _DEVICE is not None:
        return _MODEL, _TOKENIZER, _DEVICE

    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        raise ImportError(
            "Missing dependencies for DeBERTa inference. Install `torch` and `transformers`."
        ) from exc

    if not MODEL_DIR.exists():
        raise FileNotFoundError(f"Model directory not found: {MODEL_DIR}")

    _TOKENIZER = AutoTokenizer.from_pretrained(MODEL_DIR)
    _MODEL = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    _MODEL.eval()

    _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _MODEL.to(_DEVICE)

    return _MODEL, _TOKENIZER, _DEVICE


def classify_triage(text: str) -> Dict[str, float | int]:
    """
    DeBERTa ATS classification interface.

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

    import torch

    model, tokenizer, device = _load_model_and_tokenizer()

    encoded = tokenizer(
        text.strip(),
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )
    encoded = {k: v.to(device) for k, v in encoded.items()}

    with torch.no_grad():
        logits = model(**encoded).logits
        probs = torch.softmax(logits, dim=-1)[0]

    pred_idx = int(torch.argmax(probs).item())
    confidence = float(probs[pred_idx].item())

    id2label = getattr(model.config, "id2label", {}) or {}
    label_value = id2label.get(pred_idx, id2label.get(str(pred_idx), str(pred_idx + 1)))

    try:
        ats_category = int(label_value)
    except (TypeError, ValueError):
        ats_category = pred_idx + 1

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