import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

DATA_PATH = PROJECT_ROOT / "sample_data" / "scenarios.json"
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "baseline_classifier.pkl"
VECTORIZER_PATH = MODELS_DIR / "baseline_vectorizer.pkl"

samples = [
    "chest pain radiating to left arm with sweating and shortness of breath",
    "burning when urinating for 3 days, no fever, going every 10 minutes",
    "fell off skateboard, wrist pain and swelling, fingers warm and moving",
    "sudden severe headache with neck stiffness and vomiting",
    "itchy rash on both arms after gardening, no breathing trouble"
]

def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    if not VECTORIZER_PATH.exists():
        raise FileNotFoundError(f"Vectorizer file not found: {VECTORIZER_PATH}")

    classifier = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    return classifier, vectorizer


def predict_ats(text, classifier, vectorizer):
    if not text or not text.strip():
        raise ValueError("Input text cannot be empty.")

    X = vectorizer.transform([text])
    pred = classifier.predict(X)[0]

    confidence = None
    if hasattr(classifier, "predict_proba"):
        probs = classifier.predict_proba(X)[0]
        confidence = float(max(probs)) * 100
    else:
        confidence = 0.0

    return {
        "text": text,
        "predicted_ats": int(pred),
        "confidence": round(confidence, 2)
    }

def main():
    classifier, vectorizer = load_model()

    for text in samples:
        result = predict_ats(text, classifier, vectorizer)
        print("-" * 60)
        print(result)


if __name__ == "__main__":
    main()
