"""
Global FastAPI dependencies.
Domain-specific dependencies live in their own modules (e.g. api/auth/dependencies.py).
"""
from collections.abc import Generator
from functools import lru_cache
from typing import Annotated

import psycopg2
import psycopg2.extensions
import redis
from fastapi import Depends

from api.config import Settings
from api.utils.redis_client import redis_manager

# ── Settings ──────────────────────────────────────────────────────────────────

@lru_cache
def get_settings() -> Settings:
    """Cached settings — reads .env once per process."""
    return Settings()


# ── Redis ─────────────────────────────────────────────────────────────────────

def get_redis_client() -> redis.Redis:
    return redis_manager.get_client()


# ── Database ──────────────────────────────────────────────────────────────────

def get_db_conn(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Yields a psycopg2 connection per request.
    Auto-commits on success, rolls back on exception.
    FastAPI caches this dependency within the same request (use_cache=True default),
    so the same connection is reused across chained dependencies.
    """
    conn = psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Annotated aliases ─────────────────────────────────────────────────────────
# Usage: def endpoint(s: SettingsDep, db: DBConnDep): ...

SettingsDep = Annotated[Settings, Depends(get_settings)]
RedisDep = Annotated[redis.Redis, Depends(get_redis_client)]
DBConnDep = Annotated[psycopg2.extensions.connection, Depends(get_db_conn)]
