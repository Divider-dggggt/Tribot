# ATS Triage SetFit Training Project

This project trains a local SetFit text classifier for ATS 1-5 triage classification from the uploaded JSON dataset.

## What this project does

- Reads the JSON dataset at `generated_triage_dataset_200.json`
- Uses `dialogue_text` as the default model input
- Builds a stratified train / validation / test split from that single file
- Trains a SetFit classifier
- Saves:
  - the split files
  - the trained model
  - train / val / test metrics
  - confusion matrices
  - per-example prediction CSV files

## Important note about 8x4090

For a dataset this small, **data-parallel multi-GPU training is not the best use of the machine**.

The recommended setup is:

- use **one GPU per training run**
- use the remaining GPUs to run **parallel sweeps** over different sentence-transformer backbones and random seeds

That is why this repo includes:

- `train_setfit.py` for one training run
- `multi_gpu_sweep.py` to launch independent experiments across all 8 GPUs

## Recommended first run

Use the default logistic-regression SetFit head first.
That is the default SetFit head and the recommended starting point.

## Directory layout

```text
triage_setfit_project/
├── README.md
├── requirements.txt
├── train_setfit.py
├── infer.py
├── multi_gpu_sweep.py
└── scripts/
    ├── run_train.sh
    └── run_sweep_8gpu.sh
```

## 1. Create environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

If you prefer conda:

```bash
conda create -n triage-setfit python=3.10 -y
conda activate triage-setfit
pip install -r requirements.txt
```

## 2. Single-run training

```bash
bash scripts/run_train.sh /mnt/data/generated_triage_dataset_200.json runs/minilm_run
```

Equivalent direct command:

```bash
CUDA_VISIBLE_DEVICES=0 python train_setfit.py \
  --input_json /mnt/data/generated_triage_dataset_200.json \
  --output_dir runs/minilm_run \
  --model_name sentence-transformers/all-MiniLM-L6-v2 \
  --batch_size 32 \
  --num_epochs 4 \
  --num_iterations 20 \
  --seed 42 \
  --head_type logistic
```

## 3. Run 8-GPU parallel sweep

```bash
bash scripts/run_sweep_8gpu.sh /mnt/data/generated_triage_dataset_200.json runs/sweep
```

This launches one training job per GPU and writes logs + outputs into separate folders.

## 4. Try a stronger backbone

```bash
CUDA_VISIBLE_DEVICES=1 python train_setfit.py \
  --input_json /mnt/data/generated_triage_dataset_200.json \
  --output_dir runs/mpnet_run \
  --model_name sentence-transformers/all-mpnet-base-v2 \
  --batch_size 32 \
  --num_epochs 4 \
  --num_iterations 20 \
  --seed 42 \
  --head_type logistic
```

## 5. Optional differentiable head

Only try this after the logistic baseline is stable.

```bash
CUDA_VISIBLE_DEVICES=0 python train_setfit.py \
  --input_json /mnt/data/generated_triage_dataset_200.json \
  --output_dir runs/diff_head_run \
  --model_name sentence-transformers/all-MiniLM-L6-v2 \
  --batch_size 32 \
  --num_epochs 4 \
  --num_iterations 20 \
  --seed 42 \
  --head_type differentiable \
  --end_to_end
```

## 6. Inference

Single dialogue:

```bash
python infer.py \
  --model_dir runs/minilm_run/model \
  --text "Nurse: You look breathless. Patient: My asthma is much worse and I can barely speak."
```

Batch inference from JSON list:

```bash
python infer.py \
  --model_dir runs/minilm_run/model \
  --input_json sample_inputs.json \
  --output_json predictions.json
```

Accepted batch JSON formats:

```json
[
  {"text": "Nurse: ... Patient: ..."},
  {"dialogue_text": "Nurse: ... Parent: ..."}
]
```

## Output files

Each run directory contains files like:

- `run_config.json`
- `train_split.json`
- `val_split.json`
- `test_split.json`
- `train_metrics.json`
- `val_metrics.json`
- `test_metrics.json`
- `summary_metrics.json`
- `*_predictions.csv`
- `*_confusion_matrix.png`
- `model/`

## What metric to optimize

For triage, do not choose the best model only by raw accuracy.
Focus on:

- `macro_f1`
- class-wise recall for ATS 1 and ATS 2
- `under_triage_rate`

In this project:

- **under-triage** means predicted ATS number is **greater than** true ATS number
- **over-triage** means predicted ATS number is **less than** true ATS number

Examples:

- true ATS 2, predicted ATS 4 -> under-triage
- true ATS 4, predicted ATS 2 -> over-triage

## Suggested experiment order

1. `all-MiniLM-L6-v2` + logistic head
2. `all-mpnet-base-v2` + logistic head
3. `BAAI/bge-small-en-v1.5` + logistic head
4. only then test the differentiable head

## Practical caveat

This dataset looks synthetic / templated, so treat this pipeline as a solid technical baseline, not as a production-ready clinical model. Before real deployment, you would still need:

- real-world noisy triage dialogues
- external validation
- safety thresholds
- human-in-the-loop review
- rule overrides for red-flag cases
