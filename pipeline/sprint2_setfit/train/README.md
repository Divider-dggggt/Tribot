# ATS Triage SetFit Training

This project trains a SetFit classifier for ATS 1-5 triage classification from scenario-format JSON files. It is intended to run inside the shared pipeline Docker container described in `pipeline/README.md`.

## Docker Start

From the `pipeline/` directory, start the container first:

```bash
docker build -t pipeline-env .
docker run -dit -v $(pwd):/app --name pipeline-container pipeline-env
```

All commands below are run from the host with `docker exec`, while paths are relative to `/app` inside the container.

## Train

Recommended SetFit run:

```bash
docker exec -it pipeline-container python sprint2_setfit/train/train_setfit_scenarios.py \
  --input_jsons baseline_classification_model/generated_scenarios_3000.json \
  --external_val_jsons baseline_classification_model/scenarios.json \
  --output_dir sprint2_setfit/runs/minilm_run \
  --model_name sentence-transformers/all-MiniLM-L6-v2 \
  --batch_size 32 \
  --num_epochs 4 \
  --num_iterations 20 \
  --seed 42 \
  --head_type logistic \
  --strip_conclusion_lines
```

The script reads one or more labelled scenario JSON files, builds train/validation/test splits, trains a SetFit model, and evaluates train, validation, and test splits.

## Inference

After training, the trained model is saved under `final_model/` in the selected output directory. Run a single dialogue:

```bash
docker exec -it pipeline-container python sprint2_setfit/train/infer.py \
  --model_dir sprint2_setfit/runs/minilm_run/final_model \
  --text "Nurse: You look breathless. Patient: My asthma is much worse and I can barely speak."
```

Batch inference from a JSON list:

```bash
docker exec -it pipeline-container python sprint2_setfit/train/infer.py \
  --model_dir sprint2_setfit/runs/minilm_run/final_model \
  --input_json sprint2_setfit/sample_inputs.json \
  --output_json sprint2_setfit/runs/minilm_run/predictions.json
```

Accepted batch JSON records can contain either `text` or `dialogue_text`.

## Outputs

The output directory, for example `pipeline/sprint2_setfit/runs/minilm_run`, contains:

- `train_split.json`
- `val_split.json`
- `test_split.json`
- `train_metrics.json`
- `val_metrics.json`
- `test_metrics.json`
- `summary_metrics.json`
- `train_predictions.csv`
- `val_predictions.csv`
- `test_predictions.csv`
- `*_confusion.png`
- `run_config_used.json`
- `final_model/`

## Docker Stop

When finished:

```bash
docker stop pipeline-container
docker rm pipeline-container
```
