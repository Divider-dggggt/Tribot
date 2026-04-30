# Triage Scenario Data Generation

This project generates synthetic ATS triage scenarios with an OpenAI-compatible LLM. It is intended to run inside the shared pipeline Docker container described in `pipeline/README.md`.

## What It Does

`scripts/main.py` creates balanced metadata across ATS 1-5, randomly assigns a specialty and age, sends concurrent LLM requests, parses each response as JSON, and saves generated scenario records. Each generated record is expected to contain:

- `scenario_number`
- `scenario_summary_header`
- `dialogue_text`
- `ats_category`
- `ats_note`

`scripts/clean_data.py` is a small cleanup utility for a file named `scenarios_replaced.json`; it keeps only records with the exact required schema and performs a text replacement in string fields.

## Docker Start

From the `pipeline/` directory, start the container first:

```bash
docker build -t pipeline-env .
docker run -dit -v $(pwd):/app --name pipeline-container pipeline-env
```

All commands below are run from the host with `docker exec`, while paths are relative to `/app` inside the container.

## Configure LLM

Before generation, create `pipeline/data_gen/scripts/config.yaml` on the host. It will be visible inside the container at `/app/data_gen/scripts/config.yaml`.

```yaml
llm:
  url: https://your-openai-compatible-endpoint/v1
  model: your-model-name
  llm_api: your-api-key
```

`scripts/main.py` currently loads `config.yaml` from its current working directory, so the generation command must `cd` into `data_gen/scripts`.

## Generate Data

Run the generator:

```bash
docker exec -it pipeline-container sh -lc "cd /app/data_gen/scripts && python main.py"
```

Current code settings:

- total target count: `3000`
- ATS levels: `1, 2, 3, 4, 5`
- concurrent requests: `20`
- output checkpoint: every 10 successful generations

## Outputs

The active generator writes:

```text
pipeline/data_gen/scripts/generated_scenarios.json
```

There is also an existing generated dataset in:

```text
pipeline/data_gen/generated_scenarios_v3.json
```

That file contains 3000 scenario records and can be used as a generated-data artifact for downstream training.

## Cleanup Utility

If you have a file named `pipeline/data_gen/scripts/scenarios_replaced.json`, clean it with:

```bash
docker exec -it pipeline-container sh -lc "cd /app/data_gen/scripts && python clean_data.py"
```

The cleanup script overwrites `scenarios_replaced.json` in place.

## Docker Stop

When finished:

```bash
docker stop pipeline-container
docker rm pipeline-container
```
