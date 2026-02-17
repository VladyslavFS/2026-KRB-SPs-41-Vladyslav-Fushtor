"""
FastAPI dependency injection utilities.
"""
from functools import lru_cache
from typing import Annotated

import redis
from fastapi import Depends

from api.config import Settings
from api.utils.redis_client import redis_manager


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.
    Use this in FastAPI dependencies: settings: Settings = Depends(get_settings)
    """
    return Settings.from_env()


def get_redis_client() -> redis.Redis:
    """
    Get Redis client dependency.
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(redis_client: redis.Redis = Depends(get_redis_client)):
            ...
    """
    return redis_manager.get_client()


# ── Annotated dependency aliases ─────────────────────────────────────────────
# Usage: def endpoint(settings: SettingsDep, redis: RedisDep): ...

SettingsDep = Annotated[Settings, Depends(get_settings)]
RedisDep = Annotated[redis.Redis, Depends(get_redis_client)]