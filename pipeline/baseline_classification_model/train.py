import json
import csv
import joblib
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
)

BASE_DIR = Path(__file__).resolve().parent

TRAIN_DATA_PATH = BASE_DIR / "generated_scenarios_3000.json"
VAL_DATA_PATH = BASE_DIR / "scenarios.json"
TEMP_DIR = BASE_DIR / "temp"
MODELS_DIR = TEMP_DIR / "models"
EVAL_DIR = TEMP_DIR / "train_eval"

MODEL_PATH = MODELS_DIR / "baseline_classifier.pkl"
VECTORIZER_PATH = MODELS_DIR / "baseline_vectorizer.pkl"
SUMMARY_METRICS_PATH = EVAL_DIR / "summary_metrics.json"
PREDICTIONS_JSON_PATH = EVAL_DIR / "predictions.json"
PREDICTIONS_CSV_PATH = EVAL_DIR / "predictions.csv"

ATS_LABELS = [1, 2, 3, 4, 5]


def load_training_examples(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Training file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected scenarios.json to contain a list of scenario objects.")

    examples = []
    for item in data:
        if not isinstance(item, dict):
            continue

        text = item.get("dialogue_text")
        label = item.get("ats_category")
        scenario_number = item.get("scenario_number")
        summary = item.get("scenario_summary_header")

        if text is None or label is None:
            continue

        text = str(text).strip()
        if not text:
            continue

        try:
            label = int(label)
        except (TypeError, ValueError):
            continue

        if label not in ATS_LABELS:
            continue

        examples.append(
            {
                "scenario_number": scenario_number,
                "scenario_summary_header": summary,
                "text": text,
                "label": label,
            }
        )

    return examples


def build_sample_model_eval(y_true, y_pred):
    report = classification_report(
        y_true,
        y_pred,
        labels=ATS_LABELS,
        target_names=[str(x) for x in ATS_LABELS],
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=ATS_LABELS)

    weighted = report["weighted avg"]

    return {
        "sample_model_eval": {
            "f1_score": float(weighted["f1-score"]),
            "precision": float(weighted["precision"]),
            "recall": float(weighted["recall"]),
            "confusion_matrix": cm.tolist(),
        },
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "classification_report": report,
    }


def save_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def save_csv(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        with open(path, "w", encoding="utf-8", newline="") as f:
            pass
        return

    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    train_examples = load_training_examples(TRAIN_DATA_PATH)
    val_examples = load_training_examples(VAL_DATA_PATH)

    if not train_examples:
        raise ValueError("No valid training examples found in generated_scenarios_3000.json.")
    if not val_examples:
        raise ValueError("No valid validation examples found in scenarios.json.")

    X_train = [x["text"] for x in train_examples]
    y_train = [x["label"] for x in train_examples]
    X_val = [x["text"] for x in val_examples]
    y_val = [x["label"] for x in val_examples]

    print(f"Loaded {len(X_train)} training examples from {TRAIN_DATA_PATH}")
    print(f"Loaded {len(X_val)} validation examples from {VAL_DATA_PATH}")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
    )

    X_train_vec = vectorizer.fit_transform(X_train)
    X_val_vec = vectorizer.transform(X_val)

    classifier = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
    )

    classifier.fit(X_train_vec, y_train)
    y_pred = classifier.predict(X_val_vec)

    metrics = build_sample_model_eval(y_val, y_pred)

    print("\nSample model eval:")
    print(json.dumps(metrics["sample_model_eval"], ensure_ascii=False, indent=2))

    pred_rows = []
    if hasattr(classifier, "predict_proba"):
        probs = classifier.predict_proba(X_val_vec)
        max_probs = probs.max(axis=1)
    else:
        max_probs = [None] * len(y_pred)

    for i, ex in enumerate(val_examples):
        pred_rows.append(
            {
                "scenario_number": ex.get("scenario_number"),
                "scenario_summary_header": ex.get("scenario_summary_header"),
                "text": ex["text"],
                "true_ats": int(y_val[i]),
                "pred_ats": int(y_pred[i]),
                "confidence": None if max_probs[i] is None else float(max_probs[i]),
            }
        )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(classifier, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    save_json(metrics, SUMMARY_METRICS_PATH)
    save_json(pred_rows, PREDICTIONS_JSON_PATH)
    save_csv(pred_rows, PREDICTIONS_CSV_PATH)

    print(f"\nSaved model to: {MODEL_PATH}")
    print(f"Saved vectorizer to: {VECTORIZER_PATH}")
    print(f"Saved summary metrics to: {SUMMARY_METRICS_PATH}")
    print(f"Saved predictions to: {PREDICTIONS_JSON_PATH}")
    print(f"Saved predictions csv to: {PREDICTIONS_CSV_PATH}")


if __name__ == "__main__":
    main()
