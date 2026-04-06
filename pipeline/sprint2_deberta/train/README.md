# DeBERTa ATS Multiclass Classifier

This project trains a 5-way ATS classifier from scenario-format JSON files.

## Expected JSON schema
Each item should contain at least:
- `scenario_number`
- `scenario_summary_header`
- `dialogue_text`
- `ats_category`
- `ats_note` (optional, not used by default)

## Default paths
- Train: `/home/ubuntu/test/generated_scenarios.json`
- Validation: `/home/ubuntu/test/scenarios.json`
- Output: `./runs/deberta_multiclass`

## Install
```bash
conda activate test_llm
pip install -r requirements.txt
```

## Train
```bash
CUDA_VISIBLE_DEVICES=0 python train_deberta_multiclass.py \
  --train_json /home/ubuntu/test/generated_scenarios.json \
  --val_json /home/ubuntu/test/scenarios.json \
  --output_dir /home/ubuntu/test/deberta_multiclass_runs/run1
```

## Good starting tweaks
```bash
CUDA_VISIBLE_DEVICES=0 python train_deberta_multiclass.py \
  --train_json /home/ubuntu/test/generated_scenarios.json \
  --val_json /home/ubuntu/test/scenarios.json \
  --output_dir /home/ubuntu/test/deberta_multiclass_runs/run2 \
  --epochs 5 \
  --batch_size 8 \
  --grad_accum 2 \
  --lr 2e-5 \
  --max_length 512 \
  --strip_label_leakage
```

## Outputs
The output directory contains:
- `summary_metrics.json`
- `val_predictions.csv`
- `label_mapping.json`
- Hugging Face model files

## Notes
- `--strip_label_leakage` removes obvious phrases like `ATS 2`, `within 10 minutes`, `Clinical Summary`, etc.
- `--use_header` prepends `scenario_summary_header` to the dialogue text.
- Class weights are enabled by default.
