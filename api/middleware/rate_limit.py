import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis sliding window.
    
    Limits:
    - Anonymous (by IP): 60 requests/minute
    - Authenticated (by user_id): 100 requests/minute
    """
    
    def __init__(
        self,
        app,
        redis_client,
        anonymous_limit: int = 60,
        authenticated_limit: int = 100,
        window_seconds: int = 60,
        exclude_paths: list[str] = None
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.anonymous_limit = anonymous_limit
        self.authenticated_limit = authenticated_limit
        self.window_seconds = window_seconds
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable[[Request], Awaitable]
    ):
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Determine identifier and limit
        client_ip = request.client.host if request.client else "unknown"
        auth_header = request.headers.get("authorization", "")

        if auth_header.startswith("Bearer "):
            # Authenticated — key by token prefix, higher limit
            token_prefix = auth_header[7:39]  # first 32 chars
            key = f"rl:token:{token_prefix}"
            limit = self.authenticated_limit
        else:
            key = f"rl:ip:{client_ip}"
            limit = self.anonymous_limit
        
        # Check rate limit
        try:
            allowed, remaining, reset_time = await self._check_rate_limit(
                key=key,
                limit=limit,
                window=self.window_seconds
            )
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {key}. "
                    f"Reset in {reset_time - time.time():.0f}s"
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": {
                            "code": 429,
                            "message": "Rate limit exceeded. Please try again later.",
                            "retry_after": int(reset_time - time.time())
                        }
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(reset_time)),
                        "Retry-After": str(int(reset_time - time.time()))
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))
            
            return response
            
        except Exception as e:
            # If Redis fails, allow request but log error
            logger.error(f"Rate limiter error: {e}. Allowing request.")
            return await call_next(request)
    
    async def _check_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window: int
    ) -> tuple[bool, int, float]:
        """
        Sliding window rate limit check.
        
        Returns:
            (allowed, remaining_requests, reset_timestamp)
        """
        now = time.time()
        window_start = now - window
        
        # Use Redis sorted set for sliding window
        pipe = self.redis_client.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        
        # Count requests in window
        pipe.zcard(key)
        
        # Set expiry
        pipe.expire(key, window * 2)
        
        results = pipe.execute()
        count = results[2]
        
        remaining = max(0, limit - count)
        allowed = count <= limit
        reset_time = now + window
        
        return allowed, remaining, reset_time