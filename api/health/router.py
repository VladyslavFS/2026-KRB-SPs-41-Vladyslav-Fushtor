from datetime import datetime

import psycopg2
import redis as redis_lib
from fastapi import APIRouter
from pydantic import BaseModel

from api.dependencies import SettingsDep

router = APIRouter(tags=["Health"])


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    environment: str
    checks: dict[str, str]


@router.get("/health", response_model=HealthCheck)
def health_check(settings: SettingsDep) -> HealthCheck:
    """Health check — verifies DB and Redis connectivity."""
    checks: dict[str, str] = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown",
    }

    try:
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            connect_timeout=3,
        )
        conn.close()
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"

    try:
        r = redis_lib.from_url(settings.redis_url, socket_connect_timeout=3)
        r.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"

    return HealthCheck(
        status=overall,
        timestamp=datetime.utcnow(),
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