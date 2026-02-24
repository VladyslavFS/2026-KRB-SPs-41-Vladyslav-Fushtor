import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.auth.router import router as auth_router
from api.config import Settings
from api.health.router import router as health_router
from api.middleware.rate_limit import RateLimitMiddleware
from api.utils.redis_client import redis_manager
from api.v1.events.router import router as events_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = Settings()

# ── 1. Redis ──────────────────────────────────────────────────────────────────
_redis_client = None
try:
    redis_manager.initialize(settings.redis_url)
    _redis_client = redis_manager.get_client()
except Exception as e:
    logger.error(f"❌ Redis unavailable: {e}")


# ── 2. Lifespan ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 API service started")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Docs: {'enabled' if settings.app_env == 'dev' else 'disabled'}")
    logger.info(f"Rate limiting: {'enabled' if _redis_client else 'disabled'}")
    yield
    logger.info("🛑 API service shutting down...")
    redis_manager.close()


# ── 3. FastAPI app (docs only in dev) ─────────────────────────────────────────
_dev = settings.app_env == "dev"

app = FastAPI(
    title="Earthquake Platform API",
    description="Real-time earthquake monitoring and alerting system",
    version="0.1.0",
    docs_url="/docs" if _dev else None,
    redoc_url="/redoc" if _dev else None,
    openapi_url="/openapi.json" if _dev else None,
    lifespan=lifespan,
)

# ── 4. Middleware ─────────────────────────────────────────────────────────────
if _redis_client is not None:
    app.add_middleware(
        RateLimitMiddleware,
        redis_client=_redis_client,
        anonymous_limit=10,
        authenticated_limit=100,
        window_seconds=60,
    )
    logger.info("✅ Rate limiting middleware registered")
else:
    logger.warning("⚠️  Running without rate limiting")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 5. Exception handlers ─────────────────────────────────────────────────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "Validation error",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": 500, "message": "Internal server error"}},
    )


# ── 6. Routers ────────────────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(events_router)
