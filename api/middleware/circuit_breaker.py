"""
Circuit breaker pattern for protecting against cascading failures.
"""
import logging
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

import redis

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker backed by Redis for shared state across workers.

    States:
      CLOSED   → normal operation
      OPEN     → fast-fail, no calls to protected function
      HALF_OPEN → one probe call allowed to test recovery
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
    ) -> None:
        self.redis_client = redis_client
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state_key = f"cb:{name}:state"
        self._failures_key = f"cb:{name}:failures"
        self._successes_key = f"cb:{name}:successes"
        self._last_failure_key = f"cb:{name}:last_failure"

    # ── Public ────────────────────────────────────────────────────────────────

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        state = await self._get_state()

        if state == CircuitState.OPEN:
            if await self._should_attempt_reset():
                await self._set_state(CircuitState.HALF_OPEN)
                logger.info(f"Circuit '{self.name}' → HALF_OPEN")
            else:
                raise RuntimeError(f"Circuit breaker '{self.name}' is OPEN")

        try:
            result = func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as exc:
            await self._on_failure()
            raise exc

    # ── State helpers ─────────────────────────────────────────────────────────

    async def _get_state(self) -> CircuitState:
        try:
            raw = self.redis_client.get(self._state_key)
            if raw:
                value = raw.decode() if isinstance(raw, bytes) else raw
                return CircuitState(value)
            return CircuitState.CLOSED
        except Exception:
            return CircuitState.CLOSED  # fail-open

    async def _set_state(self, state: CircuitState) -> None:
        try:
            self.redis_client.set(self._state_key, state.value, ex=3600)
        except Exception as e:
            logger.error(f"Failed to set circuit state: {e}")

    async def _on_success(self) -> None:
        state = await self._get_state()

        if state == CircuitState.HALF_OPEN:
            count = self.redis_client.incr(self._successes_key)
            if count >= self.success_threshold:
                await self._set_state(CircuitState.CLOSED)
                self.redis_client.delete(self._failures_key, self._successes_key)
                logger.info(f"Circuit '{self.name}' → CLOSED (recovered)")

        elif state == CircuitState.CLOSED:
            self.redis_client.delete(self._failures_key)

    async def _on_failure(self) -> None:
        state = await self._get_state()

        if state == CircuitState.HALF_OPEN:
            await self._set_state(CircuitState.OPEN)
            self.redis_client.set(self._last_failure_key, int(time.time()), ex=3600)
            self.redis_client.delete(self._successes_key)
            logger.warning(f"Circuit '{self.name}' → OPEN (half-open probe failed)")

        elif state == CircuitState.CLOSED:
            failures = self.redis_client.incr(self._failures_key)
            self.redis_client.expire(self._failures_key, 60)

            if failures >= self.failure_threshold:
                await self._set_state(CircuitState.OPEN)
                self.redis_client.set(self._last_failure_key, int(time.time()), ex=3600)
                logger.error(
                    f"Circuit '{self.name}' → OPEN "
                    f"({failures}/{self.failure_threshold} failures)"
                )

    async def _should_attempt_reset(self) -> bool:
        try:
            raw = self.redis_client.get(self._last_failure_key)
            if not raw:
                return True
            return (time.time() - int(raw)) >= self.recovery_timeout
        except Exception:
            return True