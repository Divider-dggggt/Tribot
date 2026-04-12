from fastapi import APIRouter, Request

from app.core.config import ENCRYPTION_KEY
from app.db.connection import get_connection

router = APIRouter()


@router.get("/health")
def health(request: Request):
    checks = {
        "api": "ok",
        "database": "unknown",
        "encryption_key": "unknown",
        "routes_loaded": "unknown",
    }

    overall_status = "ok"

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
        overall_status = "degraded"

    if ENCRYPTION_KEY:
        checks["encryption_key"] = "ok"
    else:
        checks["encryption_key"] = "missing"
        overall_status = "degraded"

    try:
        route_count = len(request.app.routes)
        checks["routes_loaded"] = f"ok ({route_count} routes)"
    except Exception:
        checks["routes_loaded"] = "error"
        overall_status = "degraded"

    return {
        "status": overall_status,
        "checks": checks,
    }
