import joblib
from pathlib import Path
import json
import sys

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "baseline_classifier.pkl"
VECTORIZER_PATH = BASE_DIR / "models" / "baseline_vectorizer.pkl"


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    if not VECTORIZER_PATH.exists():
        raise FileNotFoundError(f"Vectorizer file not found: {VECTORIZER_PATH}")

    classifier = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    return classifier, vectorizer

# Load once when this module is imported
CLASSIFIER, VECTORIZER = load_model()

def predict_ats(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Input text cannot be empty.")

    cleaned_text = text.strip()
    X = VECTORIZER.transform([cleaned_text])
    pred = CLASSIFIER.predict(X)[0]

    confidence = 0.0
    if hasattr(CLASSIFIER, "predict_proba"):
        probs = CLASSIFIER.predict_proba(X)[0]
        confidence = float(max(probs)) * 100

    return {
        "input_text": cleaned_text,
        "ats_category": int(pred),
        "confidence": round(confidence, 2),
    }


# if __name__ == "__main__":
#     while True:
#         user_input = input("\nEnter symptom text (or type 'exit'): ").strip()
#         if user_input.lower() == "exit":
#             break

#         result = predict_ats(user_input)
#         print(result)

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

        result = predict_ats(input_text)
        # print(result)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        # print(e)
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()