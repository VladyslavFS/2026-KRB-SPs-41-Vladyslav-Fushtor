from contextlib import asynccontextmanager
import os
import redis.asyncio as redis
from fastapi import FastAPI
import psycopg2

redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    print(f"✅ Connected to Redis at {redis_url}")
    yield
    # Shutdown
    await redis_client.close()
    print("🛑 Redis connection closed")

app = FastAPI(title="Earthquake API", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Earthquake Platform API v1"}

@app.get("/health")
async def health():
    checks = {
        "postgres": "UNKNOWN",
        "redis": "UNKNOWN"
    }

    # 1. Check Postgres
    try:
        conn = psycopg2.connect(
            host=os.getenv("DWH_HOST", "localhost"),
            port=int(os.getenv("DWH_PORT", "5432")),
            dbname=os.getenv("DWH_DB", "earthquake"),
            user=os.getenv("DWH_USER", "postgres"),
            password=os.getenv("DWH_PASSWORD", "postgres"),
        )
        conn.close()
        checks["postgres"] = "OK"
    except Exception as e:
        checks["postgres"] = f"FAIL: {str(e)}"

    # 2. Check Redis
    try:
        await redis_client.ping()
        checks["redis"] = "OK"
    except Exception as e:
        checks["redis"] = f"FAIL: {str(e)}"

    return checks