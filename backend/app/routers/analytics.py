from datetime import date
from fastapi import APIRouter, Depends, Query
from app import db
from app.core.security import role_required

router = APIRouter()


@router.get("/analytics")
def get_analytics(
        target_date: date | None = Query(default=None, alias="date"),
        user=Depends(role_required("clinician", "admin")),
):
    return db.get_case_analytics(target_date)
