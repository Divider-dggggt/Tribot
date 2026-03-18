import joblib
from pathlib import Path

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


if __name__ == "__main__":
    while True:
        user_input = input("\nEnter symptom text (or type 'exit'): ").strip()
        if user_input.lower() == "exit":
            break

        result = predict_ats(user_input)
        print(result)
