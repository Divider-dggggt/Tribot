"""Main ATS classification benchmark runner.

Run from the project root, for example:

    python -m backend.app.services.triage_classifier.benchmark.run_benchmark \
        --input scenarios.json \
        --output-dir benchmark_outputs/scenarios \
        --models baseline deberta setfit rag \
        --lambda-under 5 \
        --lambda-over 1

Per-model failures (missing dependencies, missing API keys, etc.) are
recorded per case and the benchmark continues with the remaining models.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

from .metrics import compute_ats_metrics, normalize_ats
from .model_runners import (
    apply_rule_coverage,
    predict_with_baseline,
    predict_with_deberta,
    predict_with_rag,
    predict_with_rule,
    predict_with_setfit,
)
from .rule_energy import compute_rule_energy_from_result

PROJECT_ROOT = Path(__file__).resolve().parents[5]
BACKEND_DIR = PROJECT_ROOT / "backend"

# Known locations of the benchmark datasets (do not modify the data files).
DATA_SEARCH_DIRS = [
    Path.cwd(),
    PROJECT_ROOT,
    Path("/home/ubuntu/test"),
]

STANDARD_MODELS = ["baseline", "deberta", "setfit", "rag"]

MODEL_PREDICTORS = {
    "baseline": predict_with_baseline,
    "deberta": predict_with_deberta,
    "setfit": predict_with_setfit,
    "rag": predict_with_rag,
}


def resolve_input_path(input_arg: str) -> Path:
    """Resolve the dataset path, searching known data directories."""
    candidate = Path(input_arg)
    if candidate.exists():
        return candidate.resolve()
    if not candidate.is_absolute():
        for base in DATA_SEARCH_DIRS:
            resolved = base / candidate
            if resolved.exists():
                return resolved.resolve()
    raise FileNotFoundError(
        f"Input dataset not found: {input_arg} "
        f"(searched: {', '.join(str(d) for d in DATA_SEARCH_DIRS)})"
    )


def load_cases(
    input_path: Path,
    text_field: str,
    label_field: str,
    warnings: list[str],
) -> tuple[int, list[dict]]:
    """Load benchmark cases; skip records without usable text/gold label."""
    records = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"Expected a JSON list of records in {input_path}")

    cases = []
    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            warnings.append(f"Record {idx}: not an object, skipped.")
            continue
        text = record.get(text_field)
        if not isinstance(text, str) or not text.strip():
            warnings.append(f"Record {idx}: missing/empty '{text_field}', skipped.")
            continue
        try:
            gold = normalize_ats(record.get(label_field))
        except ValueError as exc:
            warnings.append(f"Record {idx}: invalid '{label_field}' ({exc}), skipped.")
            continue
        cases.append(
            {
                "scenario_number": str(record.get("scenario_number", idx + 1)),
                "dialogue_text": text,
                "gold_ats": gold,
            }
        )
    return len(records), cases


def _load_soap_generator(warnings: list[str]):
    """Lazily import the existing SOAP summariser without modifying it."""
    try:
        backend_dir = str(BACKEND_DIR)
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from app.services.soap_generator.summariser_service import (  # noqa: PLC0415
            generate_soap_summary,
        )

        return generate_soap_summary
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"SOAP generator unavailable: {type(exc).__name__}: {exc}")
        return None


def _load_optional_classifier(kind: str, model_path: str | None, warnings: list[str]):
    """Load an optional research classifier (ordinal / safety-cost DeBERTa)."""
    if not model_path:
        warnings.append(
            f"--include-{kind.replace('_', '-')} was set but no model path was "
            f"provided; skipping {kind}."
        )
        return None
    resolved = Path(model_path)
    if not resolved.is_absolute():
        for base in (Path.cwd(), PROJECT_ROOT):
            if (base / resolved).exists():
                resolved = base / resolved
                break
    if not resolved.exists():
        warnings.append(
            f"{kind} model path does not exist: {model_path}; skipping {kind}. "
            f"Train it explicitly first (see README)."
        )
        return None
    try:
        if kind == "ordinal_deberta":
            from .ordinal_deberta import OrdinalDebertaClassifier

            return OrdinalDebertaClassifier(resolved)
        from .safety_cost_deberta import SafetyCostDebertaClassifier

        return SafetyCostDebertaClassifier(resolved)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Failed to load {kind} model from {resolved}: {exc}")
        return None


def _predict_with_classifier(classifier, text: str) -> dict:
    result = {"ats_category": None, "confidence": None, "error": None}
    try:
        raw = classifier.predict_ats(text)
        result["ats_category"] = normalize_ats(raw["ats_category"])
        if raw.get("confidence") is not None:
            result["confidence"] = float(raw["confidence"])
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def run_cases(
    cases: list[dict],
    models: list[str],
    optional_classifiers: dict[str, object],
    include_soap: bool,
    warnings: list[str],
) -> list[dict]:
    soap_fn = _load_soap_generator(warnings) if include_soap else None

    rows = []
    total = len(cases)
    start = time.time()
    for i, case in enumerate(cases):
        text = case["dialogue_text"]
        row = {
            "scenario_number": case["scenario_number"],
            "gold_ats": case["gold_ats"],
            "dialogue_text": text,
        }

        # Rule-based severity is run once per case.
        rule_result = predict_with_rule(text)
        rule_ats = rule_result["ats_category"]
        row["rule_ats"] = rule_ats
        row["rule_error"] = rule_result["error"]

        energy = compute_rule_energy_from_result(rule_result.get("severity_result"))
        row["rule_energy"] = energy["severity_energy"]
        row["rule_energy_components"] = energy["energy_components"]
        row["rule_energy_explanation"] = energy["explanation"]

        for model in models:
            pred = MODEL_PREDICTORS[model](text)
            row[f"{model}_raw_ats"] = pred["ats_category"]
            row[f"{model}_confidence"] = pred["confidence"]
            row[f"{model}_error"] = pred["error"]
            row[f"{model}_rule_covered_ats"] = apply_rule_coverage(
                pred["ats_category"], rule_ats
            )

        for name, classifier in optional_classifiers.items():
            pred = _predict_with_classifier(classifier, text)
            row[f"{name}_raw_ats"] = pred["ats_category"]
            row[f"{name}_confidence"] = pred["confidence"]
            row[f"{name}_error"] = pred["error"]
            row[f"{name}_rule_covered_ats"] = apply_rule_coverage(
                pred["ats_category"], rule_ats
            )

        if include_soap:
            row["brief_summary"] = None
            row["soap_summary"] = None
            row["soap_error"] = None
            if soap_fn is None:
                row["soap_error"] = "SOAP generator unavailable (see warnings)."
            else:
                try:
                    soap = soap_fn(text)
                    row["brief_summary"] = soap.get("brief_summary")
                    row["soap_summary"] = soap.get("soap_markdown")
                except Exception as exc:  # noqa: BLE001
                    row["soap_error"] = f"{type(exc).__name__}: {exc}"

        rows.append(row)

        done = i + 1
        if done % 10 == 0 or done == total:
            elapsed = time.time() - start
            print(f"[benchmark] processed {done}/{total} cases ({elapsed:.1f}s)")

    return rows


def collect_prediction_columns(
    models: list[str], optional_classifiers: dict[str, object]
) -> list[str]:
    columns = []
    for model in models + list(optional_classifiers.keys()):
        columns.append(f"{model}_raw")
        columns.append(f"{model}_rule_covered")
    return columns


def compute_all_metrics(
    rows: list[dict],
    columns: list[str],
    lambda_under: float,
    lambda_over: float,
    warnings: list[str],
) -> tuple[dict, dict]:
    """Compute metrics per prediction column (only if >= 1 valid prediction)."""
    results = {}
    confusions = {}
    for column in columns:
        field = f"{column}_ats"
        pairs = [
            (row["gold_ats"], row[field])
            for row in rows
            if row.get(field) is not None
        ]
        if not pairs:
            warnings.append(f"No valid predictions for '{column}'; metrics skipped.")
            continue
        gold = [g for g, _ in pairs]
        pred = [p for _, p in pairs]
        metrics = compute_ats_metrics(
            gold, pred, lambda_under=lambda_under, lambda_over=lambda_over
        )
        confusions[column] = metrics["confusion_matrix"]
        results[column] = metrics
    return results, confusions


def summarize_rule_energy(rows: list[dict]) -> dict:
    energies = [r["rule_energy"] for r in rows if r.get("rule_energy") is not None]
    valid_rule = [r["rule_ats"] for r in rows if r.get("rule_ats") is not None]
    distribution = {str(k): 0 for k in range(1, 6)}
    for ats in valid_rule:
        distribution[str(ats)] += 1
    return {
        "average_rule_energy": (sum(energies) / len(energies)) if energies else None,
        "valid_rule_ats_percentage": 100.0 * len(valid_rule) / len(rows) if rows else 0.0,
        "rule_ats_distribution": distribution,
    }


def _fmt(value, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


MAIN_TABLE_METRICS = [
    "accuracy",
    "macro_f1",
    "weighted_f1",
    "under_triage_rate",
    "over_triage_rate",
    "critical_under_triage_rate",
    "ats_1_2_recall",
    "under_triage_severity_index",
    "squared_under_triage_severity_index",
    "mean_absolute_ordinal_error",
    "asymmetric_safety_cost_mean",
    "safety_weighted_accuracy",
]


def build_interpretation(results: dict) -> list[str]:
    lines = []
    raw_models = {k: v for k, v in results.items() if k.endswith("_raw")}
    covered_models = {k: v for k, v in results.items() if k.endswith("_rule_covered")}

    if raw_models:
        best_f1 = max(raw_models.items(), key=lambda kv: kv[1]["macro_f1"])
        lines.append(
            f"- Best raw macro-F1: `{best_f1[0]}` ({best_f1[1]['macro_f1']:.4f})."
        )
        best_swa = max(
            raw_models.items(), key=lambda kv: kv[1]["safety_weighted_accuracy"]
        )
        lines.append(
            f"- Best raw safety-weighted accuracy: `{best_swa[0]}` "
            f"({best_swa[1]['safety_weighted_accuracy']:.4f})."
        )
    if covered_models:
        lowest_under = min(
            covered_models.items(), key=lambda kv: kv[1]["under_triage_rate"]
        )
        lines.append(
            f"- Lowest rule-covered under-triage rate: `{lowest_under[0]}` "
            f"({lowest_under[1]['under_triage_rate']:.4f})."
        )

    reduced = []
    for raw_name, raw_metrics in raw_models.items():
        covered_name = raw_name.replace("_raw", "_rule_covered")
        covered = results.get(covered_name)
        if covered and covered["critical_under_triage_rate"] < raw_metrics["critical_under_triage_rate"]:
            reduced.append(
                f"{raw_name.replace('_raw', '')} "
                f"({raw_metrics['critical_under_triage_rate']:.4f} -> "
                f"{covered['critical_under_triage_rate']:.4f})"
            )
    if reduced:
        lines.append(
            "- Rule coverage reduced critical under-triage for: "
            + ", ".join(reduced)
            + "."
        )
    elif raw_models:
        lines.append(
            "- Rule coverage did not reduce critical under-triage for any model "
            "on this dataset."
        )

    if raw_models:
        best_balance = max(
            raw_models.items(),
            key=lambda kv: 0.5 * kv[1]["macro_f1"]
            + 0.5 * kv[1]["safety_weighted_accuracy"],
        )
        lines.append(
            f"- Best balance between macro-F1 and safety-weighted accuracy "
            f"(equal-weight average): `{best_balance[0]}` "
            f"(macro-F1 {best_balance[1]['macro_f1']:.4f}, "
            f"SWA {best_balance[1]['safety_weighted_accuracy']:.4f})."
        )

    lines.append(
        "- These results are technical and preliminary; they do not establish "
        "clinical validity and must not be used for clinical decision making "
        "without further validation."
    )
    return lines


def write_markdown_summary(
    output_path: Path,
    dataset_name: str,
    config: dict,
    results: dict,
    rule_energy_summary: dict,
    warnings: list[str],
) -> None:
    lines = []
    lines.append("# ATS Classification Benchmark Summary")
    lines.append("")
    lines.append("## Dataset and run configuration")
    lines.append("")
    lines.append("| Setting | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Dataset | `{dataset_name}` |")
    for key in (
        "num_cases_loaded",
        "num_cases_evaluated",
        "models_requested",
        "lambda_under",
        "lambda_over",
        "include_soap_summary",
    ):
        lines.append(f"| {key} | {config.get(key)} |")
    lines.append(
        f"| optional_research_models | {config.get('optional_research_models')} |"
    )
    lines.append("")

    lines.append("## Safety-Dominant Fusion Rule")
    lines.append("")
    lines.append(
        "The hybrid rule + model output is computed as a formal algorithm: "
        "given model prediction `y_model` and rule prediction `y_rule`, the "
        "rule-covered prediction is `y_final = min(y_model, y_rule)` when both "
        "are valid. Since lower ATS values represent higher urgency, "
        "`y_final <= y_rule` and `y_final <= y_model`, so the final output can "
        "never be less urgent than the rule-based recommendation and cannot "
        "downgrade an accepted safety signal."
    )
    lines.append("")

    lines.append("## Main model comparison")
    lines.append("")
    if results:
        header = "| model | " + " | ".join(MAIN_TABLE_METRICS) + " |"
        lines.append(header)
        lines.append("| --- |" + " --- |" * len(MAIN_TABLE_METRICS))
        for name, metrics in results.items():
            cells = " | ".join(_fmt(metrics.get(m)) for m in MAIN_TABLE_METRICS)
            lines.append(f"| {name} | {cells} |")
    else:
        lines.append("No model produced valid predictions.")
    lines.append("")

    lines.append("## Raw vs rule-covered comparison")
    lines.append("")
    lines.append(
        "| model | raw under-triage | covered under-triage | "
        "raw critical under-triage | covered critical under-triage | "
        "raw SWA | covered SWA |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    model_names = sorted(
        {k[: -len("_raw")] for k in results if k.endswith("_raw")}
    )
    for model in model_names:
        raw = results.get(f"{model}_raw", {})
        covered = results.get(f"{model}_rule_covered", {})
        lines.append(
            f"| {model} | {_fmt(raw.get('under_triage_rate'))} | "
            f"{_fmt(covered.get('under_triage_rate'))} | "
            f"{_fmt(raw.get('critical_under_triage_rate'))} | "
            f"{_fmt(covered.get('critical_under_triage_rate'))} | "
            f"{_fmt(raw.get('safety_weighted_accuracy'))} | "
            f"{_fmt(covered.get('safety_weighted_accuracy'))} |"
        )
    lines.append("")

    lines.append("## Rule energy summary")
    lines.append("")
    lines.append(
        "The rule-based severity layer is interpreted (benchmark-only) as a "
        "clinical severity energy function "
        "`E(x) = sum base_presentations + sum upward_modifiers - "
        "sum downward_modifiers + hard_override_bonus`, with "
        "`rule_ats = g(E(x))` where higher energy means greater clinical "
        "urgency."
    )
    lines.append("")
    lines.append("| Quantity | Value |")
    lines.append("| --- | --- |")
    lines.append(
        f"| Average rule energy | {_fmt(rule_energy_summary.get('average_rule_energy'))} |"
    )
    lines.append(
        f"| Cases with valid rule ATS | "
        f"{_fmt(rule_energy_summary.get('valid_rule_ats_percentage'), 2)}% |"
    )
    distribution = rule_energy_summary.get("rule_ats_distribution", {})
    dist_text = ", ".join(f"ATS {k}: {v}" for k, v in distribution.items())
    lines.append(f"| Rule ATS distribution | {dist_text} |")
    lines.append("")

    lines.append("## Interpretation (technical, preliminary)")
    lines.append("")
    lines.extend(build_interpretation(results))
    lines.append("")

    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(
    output_dir: Path,
    dataset_name: str,
    rows: list[dict],
    results: dict,
    confusions: dict,
    rule_energy_summary: dict,
    config: dict,
    warnings: list[str],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "predictions.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with (output_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            flat = {
                k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                for k, v in row.items()
            }
            writer.writerow(flat)

    summary = {
        "dataset": dataset_name,
        "num_cases_loaded": config["num_cases_loaded"],
        "num_cases_evaluated": config["num_cases_evaluated"],
        "lambda_under": config["lambda_under"],
        "lambda_over": config["lambda_over"],
        "models_requested": config["models_requested"],
        "optional_research_models": config["optional_research_models"],
        "rule_energy_summary": rule_energy_summary,
        "results": results,
        "warnings": warnings,
    }
    (output_dir / "metrics_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    (output_dir / "confusion_matrices.json").write_text(
        json.dumps(
            {"labels": [1, 2, 3, 4, 5], "confusion_matrices": confusions},
            indent=2,
        ),
        encoding="utf-8",
    )

    (output_dir / "benchmark_config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    write_markdown_summary(
        output_dir / "metrics_summary.md",
        dataset_name,
        config,
        results,
        rule_energy_summary,
        warnings,
    )


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TRIBOT ATS classification benchmark (safety-focused ordinal metrics)."
    )
    parser.add_argument("--input", required=True, help="Path to JSON dataset.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=STANDARD_MODELS,
        choices=STANDARD_MODELS,
        help="Models to run: baseline deberta setfit rag.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional case limit.")
    parser.add_argument("--lambda-under", type=float, default=5.0)
    parser.add_argument("--lambda-over", type=float, default=1.0)
    parser.add_argument("--text-field", default="dialogue_text")
    parser.add_argument("--label-field", default="ats_category")
    parser.add_argument("--include-soap-summary", action="store_true", default=False)
    parser.add_argument("--include-ordinal-deberta", action="store_true", default=False)
    parser.add_argument("--ordinal-model-path", default=None)
    parser.add_argument(
        "--include-safety-cost-deberta", action="store_true", default=False
    )
    parser.add_argument("--safety-cost-model-path", default=None)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    warnings: list[str] = []

    input_path = resolve_input_path(args.input)
    print(f"[benchmark] dataset: {input_path}")

    num_loaded, cases = load_cases(
        input_path, args.text_field, args.label_field, warnings
    )
    if args.limit is not None and args.limit >= 0:
        cases = cases[: args.limit]
    print(f"[benchmark] {num_loaded} records loaded, {len(cases)} cases to evaluate")
    if not cases:
        print("[benchmark] No usable cases; aborting.", file=sys.stderr)
        return 1

    optional_classifiers: dict[str, object] = {}
    if args.include_ordinal_deberta:
        classifier = _load_optional_classifier(
            "ordinal_deberta", args.ordinal_model_path, warnings
        )
        if classifier is not None:
            optional_classifiers["ordinal_deberta"] = classifier
    if args.include_safety_cost_deberta:
        classifier = _load_optional_classifier(
            "safety_cost_deberta", args.safety_cost_model_path, warnings
        )
        if classifier is not None:
            optional_classifiers["safety_cost_deberta"] = classifier

    rows = run_cases(
        cases,
        args.models,
        optional_classifiers,
        args.include_soap_summary,
        warnings,
    )

    columns = collect_prediction_columns(args.models, optional_classifiers)
    results, confusions = compute_all_metrics(
        rows, columns, args.lambda_under, args.lambda_over, warnings
    )
    rule_energy_summary = summarize_rule_energy(rows)

    config = {
        "input": str(input_path),
        "output_dir": args.output_dir,
        "models_requested": args.models,
        "limit": args.limit,
        "lambda_under": args.lambda_under,
        "lambda_over": args.lambda_over,
        "text_field": args.text_field,
        "label_field": args.label_field,
        "include_soap_summary": args.include_soap_summary,
        "optional_research_models": {
            "ordinal_deberta": "ordinal_deberta" in optional_classifiers,
            "safety_cost_deberta": "safety_cost_deberta" in optional_classifiers,
        },
        "ordinal_model_path": args.ordinal_model_path,
        "safety_cost_model_path": args.safety_cost_model_path,
        "num_cases_loaded": num_loaded,
        "num_cases_evaluated": len(rows),
    }

    output_dir = Path(args.output_dir)
    write_outputs(
        output_dir,
        input_path.name,
        rows,
        results,
        confusions,
        rule_energy_summary,
        config,
        warnings,
    )

    print(f"[benchmark] outputs written to {output_dir.resolve()}")
    for warning in warnings:
        print(f"[benchmark][warning] {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
