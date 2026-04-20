from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def parse_args() -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Evaluate LLM RAG ATS classification on scenarios.json."
    )
    parser.add_argument(
        "--scenarios-path",
        type=Path,
        default=base_dir.parent / "sample_data" / "scenarios.json",
        help="Path to validation scenarios.json",
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        default=base_dir / "configs" / "app_config.yaml",
        help="Path to RAG app_config.yaml",
    )
    parser.add_argument(
        "--model-key",
        type=str,
        default="rag",
        help="Top-level key name in output JSON",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Optional path to write output JSON",
    )
    return parser.parse_args()


def _evaluate(scenarios_path: Path, config_path: Path) -> dict:
    from app.services.triage_classifier.RAG.handbook_rag_function_project.pipeline import (  # noqa: E402
        llm_rag_predict,
    )

    if not scenarios_path.exists():
        raise FileNotFoundError(f"Scenarios file not found: {scenarios_path}")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
    labels = [1, 2, 3, 4, 5]

    y_true: list[int] = []
    y_pred: list[int] = []

    for sample in scenarios:
        gt = int(sample["ats_category"])
        result = llm_rag_predict(sample["dialogue_text"], str(config_path))
        pred = int(result["ats_category"])

        y_true.append(gt)
        y_pred.append(pred)

    precision, recall, f1_score, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        average="weighted",
        zero_division=0,
    )
    conf_mat = confusion_matrix(y_true, y_pred, labels=labels).tolist()

    return {
        "f1_score": float(f1_score),
        "precision": float(precision),
        "recall": float(recall),
        "confusion_matrix": conf_mat,
    }


def main() -> None:
    args = parse_args()
    eval_result = _evaluate(args.scenarios_path, args.config_path)
    output = {args.model_key: eval_result}
    output_json = json.dumps(output, ensure_ascii=False, indent=2)

    if args.output_path is not None:
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(output_json + "\n", encoding="utf-8")

    print(output_json)


if __name__ == "__main__":
    main()
