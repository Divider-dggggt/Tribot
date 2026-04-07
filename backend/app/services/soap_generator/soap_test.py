#!/usr/bin/env python3
"""
Test soap_generator using scenarios from scenarios.json.
Run from backend with PYTHONPATH=. or from repo root with PYTHONPATH=backend.
"""
from pathlib import Path
import sys
import json
import argparse
import re

# Ensure backend root (directory that contains the "app" package) is on path,
# so "from app.services.soap_generator" works when run from any cwd (e.g. Docker /app).
_app_dir = Path(__file__).resolve().parent.parent.parent  # .../app
_backend_root = _app_dir.parent  # .../backend or /app in Docker
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from app.services.soap_generator import init_soap_generator, generate_soap

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.yaml"
SCENARIOS_PATH = SCRIPT_DIR / "scenarios.json"
SOAP_FIELDS = ["subjective", "objective", "assessment", "plan"]


def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    return re.findall(r"[a-z0-9]+", text.lower())


def _lcs_length(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    n = len(b)
    prev = [0] * (n + 1)
    for ta in a:
        curr = [0] * (n + 1)
        for j, tb in enumerate(b, start=1):
            if ta == tb:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr
    return prev[n]


def rouge_l_f1(prediction: str, reference: str) -> float:
    pred_tokens = _tokenize(prediction)
    ref_tokens = _tokenize(reference)
    if not pred_tokens or not ref_tokens:
        return 0.0
    lcs = _lcs_length(pred_tokens, ref_tokens)
    precision = lcs / len(pred_tokens)
    recall = lcs / len(ref_tokens)
    if precision + recall == 0:
        return 0.0
    return (2 * precision * recall) / (precision + recall)


def _flatten_soap_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_flatten_soap_text(v) for v in value)
    if isinstance(value, dict):
        return " ".join(_flatten_soap_text(v) for v in value.values())
    return str(value)


def _generated_sections(result: dict) -> dict[str, str]:
    soap = result.get("soap", {}) if isinstance(result, dict) else {}
    subjective = soap.get("subjective", {}) if isinstance(soap, dict) else {}
    objective = soap.get("objective", {}) if isinstance(soap, dict) else {}
    return {
        "subjective": _flatten_soap_text(subjective),
        "objective": _flatten_soap_text(objective),
        "assessment": _flatten_soap_text(soap.get("assessment") if isinstance(soap, dict) else None),
        "plan": _flatten_soap_text(soap.get("plan") if isinstance(soap, dict) else None),
    }


def load_scenarios() -> list[dict]:
    if not SCENARIOS_PATH.exists():
        print(f"Scenarios file not found: {SCENARIOS_PATH}")
        sys.exit(1)
    with SCENARIOS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("scenarios.json must be a JSON array.")
        sys.exit(1)
    return data


def scenario_to_payload(s: dict) -> dict:
    """Convert one scenario object to SOAPRequest payload. ats_category may be int in JSON."""
    payload = {
        "scenario_number": s.get("scenario_number", ""),
        "scenario_summary_header": s.get("scenario_summary_header", ""),
        "dialogue_text": s.get("dialogue_text", ""),
        "ats_note": s.get("ats_note", ""),
    }
    ac = s.get("ats_category")
    if ac is not None:
        payload["ats_category"] = str(ac)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Test soap_generator with scenarios.json")
    parser.add_argument(
        "--index",
        type=int,
        default=None,
        help="Run only the scenario at this 0-based index (default: run first only)",
    )
    parser.add_argument(
        "--number",
        type=str,
        default=None,
        help="Run only the scenario with this scenario_number (e.g. 0001)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all scenarios (can be slow)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        help="When using --all, stop after this many scenarios",
    )
    parser.add_argument(
        "--eval",
        action="store_true",
        help="Evaluate generated SOAP text with ROUGE-L F1 against available references.",
    )
    args = parser.parse_args()

    if not CONFIG_PATH.exists():
        print(f"Config not found: {CONFIG_PATH}")
        sys.exit(1)

    scenarios = load_scenarios()
    if not scenarios:
        print("No scenarios in scenarios.json.")
        sys.exit(1)

    # Select which scenarios to run
    if args.number is not None:
        chosen = [s for s in scenarios if s.get("scenario_number") == args.number]
        if not chosen:
            print(f"No scenario with scenario_number={args.number!r}")
            sys.exit(1)
    elif args.index is not None:
        if args.index < 0 or args.index >= len(scenarios):
            print(f"Index {args.index} out of range (0..{len(scenarios) - 1})")
            sys.exit(1)
        chosen = [scenarios[args.index]]
    elif args.all:
        chosen = scenarios
        if args.max is not None:
            chosen = chosen[: args.max]
    else:
        chosen = [scenarios[0]]

    init_soap_generator(config_path=str(CONFIG_PATH))
    eval_scores: list[float] = []
    eval_field_scores: dict[str, list[float]] = {k: [] for k in SOAP_FIELDS}

    for i, sc in enumerate(chosen):
        num = sc.get("scenario_number", "?")
        header = sc.get("scenario_summary_header", "")[:50]
        print(f"\n--- Scenario {num} ({header}...) ---")
        payload = scenario_to_payload(sc)
        try:
            result = generate_soap(payload)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            if args.eval:
                generated_text = _flatten_soap_text(result.get("soap", {})).strip()
                reference_text = str(sc.get("dialogue_text", "")).strip()
                if not reference_text:
                    print(f"[Eval] Scenario {num} skipped: empty dialogue_text.")
                    continue

                score = rouge_l_f1(generated_text, reference_text)
                eval_scores.append(score)
                print(
                    f"[Eval] Scenario {num} SOAP-vs-dialogue ROUGE-L F1={score:.4f}"
                )

                generated_by_field = _generated_sections(result)
                field_parts: list[str] = []
                for field in SOAP_FIELDS:
                    field_score = rouge_l_f1(
                        generated_by_field.get(field, ""),
                        reference_text,
                    )
                    eval_field_scores[field].append(field_score)
                    field_parts.append(f"{field}={field_score:.4f}")
                print(
                    "[Eval-Field] SOAP-field-vs-dialogue ROUGE-L F1 "
                    + ", ".join(field_parts)
                )
        except Exception as e:
            print(f"Error: {e}")
            if not args.all:
                raise

    if args.eval:
        if eval_scores:
            avg_score = sum(eval_scores) / len(eval_scores)
            print(
                f"\n[Eval] SOAP-vs-dialogue ROUGE-L F1 mean={avg_score:.4f} "
                f"over {len(eval_scores)} scenario(s)"
            )
            field_means = []
            for field in SOAP_FIELDS:
                scores = eval_field_scores[field]
                if scores:
                    field_means.append(f"{field}={sum(scores) / len(scores):.4f}")
                else:
                    field_means.append(f"{field}=n/a")
            print("[Eval-Field] SOAP-field-vs-dialogue ROUGE-L F1 mean: " + ", ".join(field_means))
        else:
            print("\n[Eval] No scenarios had usable dialogue_text.")


if __name__ == "__main__":
    main()
