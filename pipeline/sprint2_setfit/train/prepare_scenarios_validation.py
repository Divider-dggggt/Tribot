#!/usr/bin/env python3
"""Normalize scenarios.json into the same schema used by the SetFit trainer.

Usage:
  python prepare_scenarios_validation.py \
      --input_json /home/ubuntu/test/scenarios.json \
      --output_json /home/ubuntu/test/scenarios_formatted.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_FIELDS = [
    "scenario_number",
    "scenario_summary_header",
    "dialogue_text",
    "ats_category",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize scenarios.json for triage SetFit evaluation")
    parser.add_argument("--input_json", type=str, required=True)
    parser.add_argument("--output_json", type=str, required=True)
    parser.add_argument(
        "--keep_extra_fields",
        action="store_true",
        help="Keep any extra fields such as ats_note instead of dropping them.",
    )
    return parser.parse_args()


def normalize_row(row: Dict[str, Any], idx: int, keep_extra_fields: bool) -> Dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if field not in row]
    if missing:
        raise ValueError(f"Row {idx} is missing required fields: {missing}")

    ats_category = row["ats_category"]
    if isinstance(ats_category, str):
        ats_category = ats_category.strip()
        if ats_category.isdigit():
            ats_category = int(ats_category)
    if ats_category not in {1, 2, 3, 4, 5}:
        raise ValueError(f"Row {idx} has invalid ats_category={row['ats_category']!r}")

    out = {
        "scenario_number": str(row["scenario_number"]).strip(),
        "scenario_summary_header": str(row["scenario_summary_header"]).strip(),
        "dialogue_text": str(row["dialogue_text"]).strip(),
        "ats_category": int(ats_category),
    }

    if keep_extra_fields:
        for key, value in row.items():
            if key not in out:
                out[key] = value

    return out


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_json)
    output_path = Path(args.output_json)

    with input_path.open("r", encoding="utf-8") as f:
        rows = json.load(f)

    if not isinstance(rows, list):
        raise ValueError("Expected the input JSON to be a list of scenario objects.")

    normalized: List[Dict[str, Any]] = [
        normalize_row(row, idx=i, keep_extra_fields=args.keep_extra_fields) for i, row in enumerate(rows)
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(normalized)} normalized rows to {output_path}")


if __name__ == "__main__":
    main()
