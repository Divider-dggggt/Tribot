import json
import csv
import argparse
import joblib
from pathlib import Path

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_DATA_PATH = BASE_DIR / "scenarios.json"
TEMP_DIR = BASE_DIR / "temp"
MODELS_DIR = TEMP_DIR / "models"
DEFAULT_OUTPUT_DIR = TEMP_DIR / "test_eval"

MODEL_PATH = MODELS_DIR / "baseline_classifier.pkl"
VECTORIZER_PATH = MODELS_DIR / "baseline_vectorizer.pkl"

ATS_LABELS = [1, 2, 3, 4, 5]


def parse_args():
    parser = argparse.ArgumentParser(description="Test baseline ATS classifier and export eval JSON.")
    parser.add_argument(
        "--input_json",
        type=str,
        default=str(DEFAULT_DATA_PATH),
        help="Path to evaluation JSON file",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory to save outputs",
    )
    return parser.parse_args()


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    if not VECTORIZER_PATH.exists():
        raise FileNotFoundError(f"Vectorizer file not found: {VECTORIZER_PATH}")

    classifier = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    return classifier, vectorizer


def load_eval_examples(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Evaluation file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected evaluation JSON to contain a list of objects.")

    rows = []
    for item in data:
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

        if label not in ATS_LABELS:
            continue

        rows.append(
            {
                "scenario_number": item.get("scenario_number"),
                "scenario_summary_header": item.get("scenario_summary_header"),
                "text": text,
                "label": label,
            }
        )

    return rows


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
    args = parse_args()
    input_path = Path(args.input_json)
    output_dir = Path(args.output_dir)

    classifier, vectorizer = load_model()
    rows = load_eval_examples(input_path)

    if not rows:
        raise ValueError("No valid evaluation examples found.")

    texts = [r["text"] for r in rows]
    y_true = [r["label"] for r in rows]

    X = vectorizer.transform(texts)
    y_pred = classifier.predict(X)

    metrics = build_sample_model_eval(y_true, y_pred)

    if hasattr(classifier, "predict_proba"):
        probs = classifier.predict_proba(X)
        max_probs = probs.max(axis=1)
    else:
        max_probs = [None] * len(y_pred)

    pred_rows = []
    for i, row in enumerate(rows):
        pred_rows.append(
            {
                "scenario_number": row.get("scenario_number"),
                "scenario_summary_header": row.get("scenario_summary_header"),
                "text": row["text"],
                "true_ats": int(y_true[i]),
                "pred_ats": int(y_pred[i]),
                "confidence": None if max_probs[i] is None else float(max_probs[i]),
            }
        )

    save_json(metrics, output_dir / "summary_metrics.json")
    save_json(pred_rows, output_dir / "predictions.json")
    save_csv(pred_rows, output_dir / "predictions.csv")

    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"[done] wrote metrics to {output_dir / 'summary_metrics.json'}")


if __name__ == "__main__":
    main()
