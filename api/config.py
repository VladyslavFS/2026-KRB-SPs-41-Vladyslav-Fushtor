from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """
    Unified configuration for API service.
    Replaces scattered configs from pipeline.config
    """
    app_env: str  # dev | prod
    
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    
    redis_url: str
    
    storage_backend: str  # minio | s3
    s3_bucket: str
    s3_endpoint: str | None
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    aws_region: str
    
    cors_origins: list[str]
    
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int
    
    @staticmethod
    def from_env() -> Settings:
        """Load configuration from environment variables"""
        
        # Parse CORS origins
        cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000")
        cors_origins = [origin.strip() for origin in cors_origins_raw.split(",")]
        
        return Settings(
            # Application
            app_env=os.getenv("APP_ENV", "dev"),
            
            # Database
            db_host=os.getenv("DWH_HOST", "localhost"),
            db_port=int(os.getenv("DWH_PORT", "5432")),
            db_name=os.getenv("DWH_DB", "earthquake"),
            db_user=os.getenv("DWH_USER", "postgres"),
            db_password=os.getenv("DWH_PASSWORD", "postgres"),
            
            # Redis
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            
            # Storage
            storage_backend=os.getenv("STORAGE_BACKEND", "minio"),
            s3_bucket=os.getenv("S3_BUCKET", "lake"),
            s3_endpoint=os.getenv("S3_ENDPOINT") or None,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID") or None,
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY") or None,
            aws_region=os.getenv("AWS_REGION", "eu-north-1"),
            
            # API
            cors_origins=cors_origins,
            
            # JWT
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")),
        )
    
    @property
    def database_url(self) -> str:
        """PostgreSQL connection string"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"