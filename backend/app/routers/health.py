from fastapi import APIRouter, Request
from app.db.connection import get_connection

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "backend",
        "message": "API is running",
    }

@router.get("/health/ready")
def readiness():
    checks = {
        "api": "ok",
        "database": "unknown",
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
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        overall_status = "degraded"

    return {
        "status": overall_status,
        "checks": checks,
    }

@router.get("/health/routes")
def list_routes(request: Request):
    routes = []
    for route in request.app.routes:
        methods = sorted(list(route.methods)) if hasattr(route, "methods") else []
        routes.append(
            {
                "path": route.path,
                "methods": methods,
                "name": route.name,
            }
        )

    return {
        "status": "ok",
        "route_count": len(routes),
        "routes": routes,
    }
