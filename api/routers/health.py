from datetime import datetime

import psycopg2
import redis
from fastapi import APIRouter
from pydantic import BaseModel

from api.dependencies import SettingsDep

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str
    timestamp: datetime
    version: str
    environment: str
    checks: dict


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: SettingsDep):
    """
    Health check endpoint.
    Returns service status and dependency health.
    """
    checks = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown"
    }
    
    # Check database connection
    try:
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            connect_timeout=3
        )
        conn.close()
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    
    # Check Redis connection
    try:
        r = redis.from_url(settings.redis_url, socket_connect_timeout=3)
        r.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    # Overall status
    overall_status = "healthy" if all(
        v == "healthy" for v in checks.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="0.1.0",
        environment=settings.app_env,
        checks=checks
    )


@router.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "service": "Earthquake Platform API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }