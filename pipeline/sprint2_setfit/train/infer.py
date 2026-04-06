#!/usr/bin/env python3
"""Inference script for the trained SetFit ATS triage model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from setfit import SetFitModel


INDEX_TO_LABEL = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run inference with a trained SetFit ATS model")
    parser.add_argument("--model_dir", type=str, required=True)
    parser.add_argument("--text", type=str, default=None, help="Single triage dialogue string")
    parser.add_argument("--input_json", type=str, default=None, help="JSON file with a list of records or strings")
    parser.add_argument("--output_json", type=str, default=None)
    return parser.parse_args()


def load_inputs(args: argparse.Namespace) -> List[dict]:
    if args.text:
        return [{"text": args.text}]
    if not args.input_json:
        raise ValueError("Provide either --text or --input_json")
    with open(args.input_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        rows = []
        for item in data:
            if isinstance(item, str):
                rows.append({"text": item})
            elif isinstance(item, dict):
                if "text" in item:
                    rows.append(item)
                elif "dialogue_text" in item:
                    rows.append({**item, "text": item["dialogue_text"]})
                else:
                    raise ValueError("Each dict item must have 'text' or 'dialogue_text'.")
            else:
                raise ValueError("Unsupported item type in input JSON list.")
        return rows
    raise ValueError("input_json must contain a JSON list.")


def main() -> None:
    args = parse_args()
    model = SetFitModel.from_pretrained(args.model_dir)
    rows = load_inputs(args)
    texts = [row["text"] for row in rows]

    preds = model.predict(texts)
    probs = None
    if hasattr(model.model_head, "predict_proba"):
        embeddings = model.model_body.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        probs = model.model_head.predict_proba(embeddings)

    results = []
    for idx, row in enumerate(rows):
        result = dict(row)
        pred_idx = int(preds[idx])
        result["pred_label_index"] = pred_idx
        result["pred_ats_category"] = INDEX_TO_LABEL[pred_idx]
        if probs is not None:
            result["probabilities"] = {
                str(INDEX_TO_LABEL[class_idx]): float(prob) for class_idx, prob in enumerate(probs[idx])
            }
        results.append(result)

    output = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output_json:
        Path(args.output_json).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
