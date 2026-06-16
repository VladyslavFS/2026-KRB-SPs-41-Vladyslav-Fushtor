from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from api.dependencies import DBConnDep, RedisDep, SettingsDep

router = APIRouter(tags=["Health"])


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    environment: str
    checks: dict[str, str]


@router.get("/health", response_model=HealthCheck)
def health_check(
    settings: SettingsDep,
    db: DBConnDep,
    redis_client: RedisDep,
) -> HealthCheck:
    """Health check — verifies DB and Redis connectivity."""
    checks: dict[str, str] = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown",
    }

    try:
        with db.cursor() as cur:
            cur.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"

    try:
        redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"

    return HealthCheck(
        status=overall,
        timestamp=datetime.now(UTC),
        version="0.1.0",
        environment=settings.app_env,
        checks=checks,
    )


@router.get("/", include_in_schema=False)
def root() -> dict:
    return {
        "service": "Earthquake Platform API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }