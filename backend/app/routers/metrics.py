import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import admin_required

router = APIRouter()

MODEL_EVAL_PATH = (
        Path(__file__).resolve().parent.parent
        / "services"
        / "triage_classifier"
        / "models"
        / "model_eval.json"
)


@router.get("/model-metrics/{model_name}")
def get_model_metrics(model_name: str, admin=Depends(admin_required)):
    with MODEL_EVAL_PATH.open() as f:
        data = json.load(f)

    if model_name not in data:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "model_name": model_name,
        "metrics": data[model_name],
    }
