# SOAP Triage Benchmark Package

This package is a **section-aware, fact-aware, safety-aware benchmark** for evaluating SOAP note generation from emergency triage dialogue.

It was designed around your current generator schema:

- `subjective`
- `objective`
- `assessment`
- `plan`
- `brief_summary`

and around your uploaded triage scenarios plus the ETEK handbook.

## What is included

- `data/gold_annotations.json`
- `data/challenge_set.json`
- `data/scenarios.json`
- `benchmark/`
- `scripts/build_handbook_index.py`
- `scripts/evaluate_generated_json.py`
- `scripts/build_gold_from_scenarios.py`

## Benchmark design

Main score:
1. Structure validity
2. Must-fact recall
3. Supported fact precision
4. Section placement accuracy
5. Clinical adequacy
6. Safety

Handbook alignment is scored separately using local retrieval against the uploaded ETEK PDF.

## Quick start

Build the handbook index:

```bash
python scripts/build_handbook_index.py \
  --pdf /path/to/emergency_triage_education_kit_-_second_edition.pdf \
  --out_dir data/handbook_index
```

Evaluate generated SOAP outputs:

```bash
python scripts/evaluate_generated_json.py \
  --gold data/gold_annotations.json \
  --pred generated_outputs.json \
  --handbook_dir data/handbook_index \
  --out_json evaluation_results.json
```

Evaluate only the challenge set:

```bash
python scripts/evaluate_generated_json.py \
  --gold data/gold_annotations.json \
  --pred generated_outputs.json \
  --challenge data/challenge_set.json
```

## Notes

- The ETEK is a **triage** handbook, not a SOAP handbook, so handbook alignment is treated as an **auxiliary metric**, not the main score.
- The gold annotations are designed to match your current schema and triage-task setting.
- The benchmark can be reused with real data by replacing the gold annotations file.


## Final output
backend/app/services/soap_generator/benchmark/data/evaluation_results_generated_samples.json
