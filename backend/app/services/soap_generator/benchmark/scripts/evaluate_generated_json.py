#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from benchmark.scoring import evaluate_predictions


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate generated SOAP JSON against the benchmark gold file.")
    parser.add_argument("--gold", required=True, help="Path to gold_annotations.json")
    parser.add_argument("--pred", required=True, help="Path to generated predictions JSON")
    parser.add_argument("--handbook_dir", default=None, help="Optional handbook index directory")
    parser.add_argument("--challenge", default=None, help="Optional challenge_set.json")
    parser.add_argument("--out_json", default=None, help="Optional output JSON path")
    args = parser.parse_args()

    challenge_ids = None
    if args.challenge:
        challenge_ids = json.loads(open(args.challenge, "r", encoding="utf-8").read())["challenge_ids"]

    results = evaluate_predictions(
        gold_path=args.gold,
        pred_path=args.pred,
        handbook_dir=args.handbook_dir,
        challenge_ids=challenge_ids,
    )

    print(json.dumps(results["summary"], indent=2))
    if args.out_json:
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nFull results written to {args.out_json}")


if __name__ == "__main__":
    main()
