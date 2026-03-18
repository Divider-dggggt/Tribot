#!/usr/bin/env python3
"""
Test soap_generator using scenarios from scenarios.json.
Run from backend with PYTHONPATH=. or from repo root with PYTHONPATH=backend.
"""
from pathlib import Path
import sys
import json
import argparse

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

    for i, sc in enumerate(chosen):
        num = sc.get("scenario_number", "?")
        header = sc.get("scenario_summary_header", "")[:50]
        print(f"\n--- Scenario {num} ({header}...) ---")
        payload = scenario_to_payload(sc)
        try:
            result = generate_soap(payload)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Error: {e}")
            if not args.all:
                raise


if __name__ == "__main__":
    main()