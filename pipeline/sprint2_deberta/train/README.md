# DeBERTa ATS Multiclass Classifier

This project trains a 5-way DeBERTa-based ATS classifier from scenario-format JSON files. It is intended to run inside the shared pipeline Docker container described in `pipeline/README.md`.

## Expected JSON Schema

Each item should contain at least:

- `scenario_number`
- `scenario_summary_header`
- `dialogue_text`
- `ats_category`
- `ats_note` optional

## Docker Start

From the `pipeline/` directory, start the container first:

```bash
docker build -t pipeline-env .
docker run -dit -v $(pwd):/app --name pipeline-container pipeline-env
```

All commands below are run from the host with `docker exec`, while paths are relative to `/app` inside the container.

## Train

Recommended first run:

```bash
docker exec -it pipeline-container python sprint2_deberta/train/train_deberta_multiclass.py \
  --train_json baseline_classification_model/generated_scenarios_3000.json \
  --val_json baseline_classification_model/scenarios.json \
  --output_dir sprint2_deberta/runs/deberta_multiclass/run1 \
  --model_name microsoft/deberta-v3-base \
  --epochs 4 \
  --batch_size 8 \
  --grad_accum 1 \
  --lr 2e-5 \
  --max_length 384 \
  --strip_label_leakage
```

Smaller smoke-test run for checking wiring without committing to a full training job:

```bash
docker exec -it pipeline-container python sprint2_deberta/train/train_deberta_multiclass.py \
  --train_json baseline_classification_model/generated_scenarios_3000.json \
  --val_json baseline_classification_model/scenarios.json \
  --output_dir sprint2_deberta/runs/deberta_multiclass/smoke \
  --model_name microsoft/deberta-v3-base \
  --epochs 1 \
  --batch_size 2 \
  --eval_batch_size 2 \
  --grad_accum 1 \
  --max_length 128 \
  --strip_label_leakage
```

## Outputs

The output directory, for example `pipeline/sprint2_deberta/runs/deberta_multiclass/run1`, contains:

- `summary_metrics.json`
- `val_predictions.csv`
- `label_mapping.json`
- `run_args.json`
- `best_model/`
- Hugging Face trainer checkpoint folders

## Notes

- `--strip_label_leakage` removes obvious label hints such as `ATS 2`, `within 10 minutes`, and `Clinical Summary`.
- `--use_header` prepends `scenario_summary_header` to the dialogue text.
- Class weights are enabled by default. Use `--no_class_weights` only for ablation.

## Docker Stop

When finished:

```bash
docker stop pipeline-container
docker rm pipeline-container
```
