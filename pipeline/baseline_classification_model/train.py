import json
import joblib
from pathlib import Path
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

DATA_PATH = PROJECT_ROOT / "sample_data" / "scenarios.json"
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "baseline_classifier.pkl"
VECTORIZER_PATH = MODELS_DIR / "baseline_vectorizer.pkl"

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Training file not found: {DATA_PATH}")

def load_training_examples(path):
    if not path.exists():
        raise FileNotFoundError(f"Training file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected scenarios.json to contain a list of scenario objects.")

    examples = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        text = item.get("dialogue_text")
        label = item.get("ats_category")

        if text is None or label is None:
            continue

        text = str(text).strip()
        if not text:
            continue

        try:
            label = int(label)
        except (TypeError, ValueError):
            continue

        examples.append((text, label))

    return examples


def main():
    examples = load_training_examples(DATA_PATH)

    if not examples:
        raise ValueError("No valid training examples found in scenarios.json.")

    texts = [x[0] for x in examples]
    labels = [x[1] for x in examples]

    print(f"Loaded {len(texts)} training examples")

    label_counts = Counter(labels)
    min_class_count = min(label_counts.values())
    print("Label distribution:", dict(label_counts))
    if min_class_count >= 2:
        X_train, X_test, y_train, y_test = train_test_split(
            texts,
            labels,
            test_size=0.2,
            random_state=42,
            stratify=labels
        )
        print("Using stratified train/test split.")
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            texts,
            labels,
            test_size=0.2,
            random_state=42
        )
        print("Using non-stratified train/test split because at least one class has fewer than 2 samples.")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1
    )

    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    classifier = LogisticRegression(
        max_iter=2000,
        class_weight="balanced"
    )

    classifier.fit(X_train_vec, y_train)

    y_pred = classifier.predict(X_test_vec)

    print("\nAccuracy:")
    print(accuracy_score(y_test, y_pred))

    print("\nClassification report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(classifier, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    print(f"\nSaved model to: {MODEL_PATH}")
    print(f"Saved vectorizer to: {VECTORIZER_PATH}")


if __name__ == "__main__":
    main()
