# Handbook RAG Function Project

Lightweight ATS handbook retrieval, handbook-fit normalization, and LLM-based handbook-grounded triage inference. The main Docker-tested function is `llm_rag_predict(query_txt: str, config_path: str) -> dict`, which returns an ATS category, confidence, and handbook-grounded citation. This repository is Docker-based, so start the full project from the repository root with `docker compose up --build -d` before running RAG commands. The backend service is mounted at `/app`, and this RAG directory is available inside the container at `/app/app/services/triage_classifier/RAG`.

## Configure

Edit `backend/app/services/triage_classifier/RAG/configs/app_config.yaml` and `backend/app/services/triage_classifier/RAG/configs/llm_config.yaml` on the host. If `app_config.yaml` needs to be recreated from the example, run:

```bash
docker compose exec -T backend sh -lc "cd /app/app/services/triage_classifier/RAG && cp configs/app_config.example.yaml configs/app_config.yaml"
```

Set the handbook PDF path, artifact paths, LLM config path, and optional local model settings in `app_config.yaml`. Set the LLM URL/model in `llm_config.yaml`; the API key is provided to the container through `LLM_API_KEY` from the project `.env`.

## Build Handbook Indices

```bash
docker compose exec -T backend sh -lc "cd /app/app/services/triage_classifier/RAG && python -c \"from handbook_rag_function_project.pipeline import ingest_handbook; print(ingest_handbook('configs/app_config.yaml'))\""
```

## Call LLM / RAG Branch

```bash
docker compose exec -T backend sh -lc "cd /app/app/services/triage_classifier/RAG && python -" <<'PY'
from handbook_rag_function_project.pipeline import llm_rag_predict

result = llm_rag_predict(
    "28 weeks pregnant, severe headache, visual disturbance, vomiting, BP 180/115.",
    "configs/app_config.yaml"
)
print(result)
PY
```

Example output:

```python
{
  "ats_category": 2,
  "confidence": 0.95,
  "citation": "ETEK p.94 Chapter 6: Pregnancy / Red flags - Symptoms suggestive of pre-eclampsia, such as hypertension, visual disturbances, persistent headache"
}
```
