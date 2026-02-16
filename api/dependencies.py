from functools import lru_cache

from api.config import Settings


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    Use this in FastAPI dependencies: settings: Settings = Depends(get_settings)
    """
    return Settings.from_env()