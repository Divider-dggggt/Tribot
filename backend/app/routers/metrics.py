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

MODEL_NAME = "sample_model_eval"

@router.get("/model-metrics")
def get_model_metrics(admin=Depends(admin_required)):
    with MODEL_EVAL_PATH.open() as f:
        data = json.load(f)

    return {
        "model_name": MODEL_NAME,
        "metrics": data[MODEL_NAME],
    }
