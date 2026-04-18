# Handbook RAG Function Project

Lightweight ATS handbook retrieval + handbook-fit normalization + dual branch inference as plain Python function calls.

## Main functions

- `ingest_handbook(config_path: str) -> dict`
- `local_predict(query_txt: str, config_path: str) -> dict`
- `llm_rag_predict(query_txt: str, config_path: str) -> dict`

## Output formats

### local_predict
```python
{
  "ats_category": 2,
  "confidence": 0.84
}
```

### llm_rag_predict
```python
{
  "ats_category": 2,
  "confidence": 0.78,
  "citation": "ETEK p.23 Table 2.1: severe respiratory distress maps to a high triage category."
}
```

## Install

```bash
conda activate test_llm
pip install -r requirements.txt
```

## Configure

Copy and edit:

```bash
cp configs/app_config.example.yaml configs/app_config.yaml
```

Set the handbook PDF path, the LLM config path, and optionally either:
- a Hugging Face sequence-classifier model directory, or
- a sklearn TF-IDF + logistic regression baseline pair.

## Build handbook indices

```bash
python -c "from handbook_rag_function_project.pipeline import ingest_handbook; print(ingest_handbook('configs/app_config.yaml'))"
```

### Docker (from repository root)

```bash
docker compose exec -w /app/app/services/RAG backend python -c "from handbook_rag_function_project.pipeline import ingest_handbook; print(ingest_handbook('configs/app_config.yaml'))"
```

## Call local branch

```bash
python - <<'PY'
from handbook_rag_function_project.pipeline import local_predict

result = local_predict(
    "28 weeks pregnant, severe headache, visual disturbance, vomiting, BP 180/115.",
    "configs/app_config.yaml"
)
print(result)
PY
```

## Call LLM / RAG branch

```bash
python - <<'PY'
from handbook_rag_function_project.pipeline import llm_rag_predict

result = llm_rag_predict(
    "28 weeks pregnant, severe headache, visual disturbance, vomiting, BP 180/115.",
    "configs/app_config.yaml"
)
print(result)
PY
```
