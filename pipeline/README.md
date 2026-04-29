## to run pipeline

This Docker environment is separate from the main project stack started by `docker compose up --build` at the repository root. The main stack runs the frontend, backend, and database. The pipeline stack is a standalone training/data-generation container built from `pipeline/Dockerfile`.

### start
```
docker build -t pipeline-env .
docker run -dit -v $(pwd):/app --name pipeline-container pipeline-env
docker exec -it pipeline-container bash
```

Command details:

- `docker build -t pipeline-env .`
  - Builds the pipeline Docker image from `pipeline/Dockerfile`.
  - Installs Python training dependencies such as scikit-learn, transformers, torch, SetFit, datasets, pandas, and matplotlib.
  - Output: a local Docker image named `pipeline-env`.
  - Warning: the first build can take a long time because torch and related ML packages are large. Re-running this command rebuilds the image if files used by the Docker build have changed.

- `docker run -dit -v $(pwd):/app --name pipeline-container pipeline-env`
  - Starts a detached interactive container named `pipeline-container`.
  - Mounts the current `pipeline/` directory into the container at `/app`, so files produced inside `/app` are written back to the host `pipeline/` directory.
  - Output: a running container named `pipeline-container`.
  - Warning: this command fails if a container with the same name already exists. If that happens, run the `### stop` commands first.

- `docker exec -it pipeline-container bash`
  - Opens an interactive shell inside the already-running pipeline container.
  - Use this only if you want to type commands manually inside the container.
  - Warning: if you use the documented `docker exec ... python ...` commands below from the host, you do not need to enter this shell.

### run any
```
python baseline_classification_model/train.py
```

Command details:

- `python baseline_classification_model/train.py`
  - Runs the baseline classifier training script from inside the container shell.
  - This command assumes you already ran `docker exec -it pipeline-container bash` and are now inside `/app`.
  - Output: baseline training metrics printed to the terminal; any model artifacts depend on the baseline script implementation.
  - Warning: this is the generic example command. For SetFit, DeBERTa, and data generation, prefer the specific `### run ...` sections below.

### stop
```
docker stop pipeline-container
docker rm pipeline-container
```

Command details:

- `docker stop pipeline-container`
  - Stops the running pipeline container.
  - Output: the stopped container name.
  - Warning: this does not delete files written under the mounted `pipeline/` directory on the host.

- `docker rm pipeline-container`
  - Removes the stopped container so a future `docker run --name pipeline-container ...` can reuse the same name.
  - Output: the removed container name.
  - Warning: this removes only the container, not the `pipeline-env` image and not generated files in the host `pipeline/` directory.

## train results

### baseline
```
Loaded 50 training examples
Label distribution: {2: 22, 3: 19, 4: 8, 1: 1}
Using non-stratified train/test split because at least one class has fewer than 2 samples.

Accuracy:
0.7

Classification report:
              precision    recall  f1-score   support

           2       0.60      1.00      0.75         3
           3       0.80      0.80      0.80         5
           4       0.00      0.00      0.00         2

    accuracy                           0.70        10
   macro avg       0.47      0.60      0.52        10
weighted avg       0.58      0.70      0.62        10
```

### run setfit
After the shared `### start` commands have created `pipeline-container`, run SetFit training from the repository host:

```
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

Command details:

- This command runs `sprint2_setfit/train/train_setfit_scenarios.py` inside `pipeline-container`.
- `--input_jsons baseline_classification_model/generated_scenarios_3000.json` uses the generated labelled scenarios as the training/test source.
- `--external_val_jsons baseline_classification_model/scenarios.json` uses the smaller shared scenario file as external validation.
- `--output_dir sprint2_setfit/runs/minilm_run` controls where all SetFit outputs are saved.
- `--model_name sentence-transformers/all-MiniLM-L6-v2` downloads/uses the MiniLM sentence-transformer backbone.
- `--strip_conclusion_lines` removes obvious triage conclusion/routing lines to reduce label leakage.

SetFit outputs are written under:

```
sprint2_setfit/runs/minilm_run
```

Expected outputs include:

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

Warning: if you re-run the same command with the same `--output_dir`, files in `sprint2_setfit/runs/minilm_run` can be overwritten or mixed with the new run. Use a new output directory such as `sprint2_setfit/runs/minilm_run_2` to keep previous results.

Run SetFit inference after training:

```
docker exec -it pipeline-container python sprint2_setfit/train/infer.py \
  --model_dir sprint2_setfit/runs/minilm_run/final_model \
  --text "Nurse: You look breathless. Patient: My asthma is much worse and I can barely speak."
```

Command details:

- This loads the trained SetFit model from `sprint2_setfit/runs/minilm_run/final_model`.
- It predicts the ATS category for the single text supplied through `--text`.
- Output: prediction JSON printed to the terminal.
- Warning: this command requires the training command to have completed successfully first. If `final_model/` does not exist, inference fails.

Then use the shared `### stop` commands when finished.

### run deberta
After the shared `### start` commands have created `pipeline-container`, run DeBERTa training from the repository host:

```
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

Command details:

- This command runs `sprint2_deberta/train/train_deberta_multiclass.py` inside `pipeline-container`.
- `--train_json baseline_classification_model/generated_scenarios_3000.json` uses generated labelled scenarios for training.
- `--val_json baseline_classification_model/scenarios.json` uses the smaller scenario file for validation.
- `--output_dir sprint2_deberta/runs/deberta_multiclass/run1` controls where checkpoints, metrics, predictions, and the best model are saved.
- `--model_name microsoft/deberta-v3-base` downloads/uses the DeBERTa v3 base model.
- `--strip_label_leakage` removes explicit ATS hints from the input text before training/evaluation.

DeBERTa outputs are written under:

```
sprint2_deberta/runs/deberta_multiclass/run1
```

Expected outputs include:

- `summary_metrics.json`
- `val_predictions.csv`
- `label_mapping.json`
- `run_args.json`
- `best_model/`
- Hugging Face trainer checkpoint folders

Warning: if you re-run the same command with the same `--output_dir`, trainer checkpoints and output files in `sprint2_deberta/runs/deberta_multiclass/run1` can be overwritten or mixed with the new run. Use a new output directory such as `run2` to preserve previous results. Full DeBERTa training is compute-heavy and may download model weights on first run.

For a lighter wiring check, reduce the run:

```
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

Command details:

- This is a smaller DeBERTa run intended to check that the script, dataset paths, model download, and output path work.
- It still starts a real training job, but with fewer epochs, smaller batch sizes, and shorter max sequence length.
- Output: written to `sprint2_deberta/runs/deberta_multiclass/smoke`.
- Warning: this is still not a zero-cost command. It can take time and may overwrite previous smoke-test outputs if re-run with the same output directory.

Then use the shared `### stop` commands when finished.

### run data_gen
After the shared `### start` commands have created `pipeline-container`, create `data_gen/scripts/config.yaml` with the LLM endpoint, model, and API key:

```
llm:
  url: https://your-openai-compatible-endpoint/v1
  model: your-model-name
  llm_api: your-api-key
```

Command details:

- This YAML file is read by `data_gen/scripts/main.py`.
- `url` should be the OpenAI-compatible API base URL.
- `model` should be the model name accepted by that endpoint.
- `llm_api` should be the API key used by the generator.
- Warning: do not commit real API keys. If this file already exists, editing it changes which provider/model the generator will call.

Run data generation from the repository host:

```
docker exec -it pipeline-container sh -lc "cd /app/data_gen/scripts && python main.py"
```

Command details:

- This changes into `/app/data_gen/scripts` because `main.py` expects `config.yaml` in the current working directory.
- It runs the asynchronous LLM scenario generator.
- Current code target: `3000` generated scenarios.
- Current concurrency: `20` requests at a time.
- Output checkpoint: every 10 successful generations.
- Warning: this can consume substantial API quota and time. Stop it early with `Ctrl+C` if you only need to confirm it starts.

The generator writes checkpoints every 10 successful generations to:

```
data_gen/scripts/generated_scenarios.json
```

Warning: re-running `main.py` overwrites `data_gen/scripts/generated_scenarios.json` whenever another 10 successful generations are saved. Move or rename that file before re-running if you need to keep the previous output.

The existing generated dataset is:

```
data_gen/generated_scenarios_v3.json
```

This existing file contains 3000 scenario records and is not written by the current `main.py` command. It is a ready-to-use generated data artifact for downstream training.

Run the cleanup utility only when `data_gen/scripts/scenarios_replaced.json` exists:

```
docker exec -it pipeline-container sh -lc "cd /app/data_gen/scripts && python clean_data.py"
```

Command details:

- This runs `data_gen/scripts/clean_data.py`.
- It expects `data_gen/scripts/scenarios_replaced.json`.
- It keeps only records with the exact required scenario schema and performs the configured string replacement.
- Output: `data_gen/scripts/scenarios_replaced.json` is overwritten in place.
- Warning: this command is destructive for `scenarios_replaced.json`. Make a copy first if you need the original file.

Then use the shared `### stop` commands when finished.
