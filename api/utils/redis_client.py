"""
Redis client singleton with connection pooling.
"""
import logging

import redis
from redis.connection import ConnectionPool

logger = logging.getLogger(__name__)


class RedisClient:
    """Singleton Redis client with connection pooling."""

    _instance: "RedisClient | None" = None
    _client: redis.Redis | None = None

    def __new__(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, redis_url: str, **kwargs) -> None:
        if self._client is not None:
            logger.warning("Redis client already initialized")
            return

        pool = ConnectionPool.from_url(
            redis_url,
            max_connections=20,
            decode_responses=False,
            socket_timeout=5,
            socket_connect_timeout=5,
            **kwargs,
        )
        self._client = redis.Redis(connection_pool=pool)
        self._client.ping()
        logger.info(f"✅ Redis client initialized: {redis_url}")

    def get_client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError("Redis client not initialized. Call initialize() first.")
        return self._client

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Redis connection closed")


redis_manager = RedisClient()