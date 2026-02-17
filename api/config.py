"""
Application settings via pydantic-settings.
"""
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = Field("dev", alias="APP_ENV")

    # ── Database ──────────────────────────────────────────────────────────────
    db_host: str = Field("localhost", alias="DWH_HOST")
    db_port: int = Field(5432, alias="DWH_PORT")
    db_name: str = Field("earthquake", alias="DWH_DB")
    db_user: str = Field("postgres", alias="DWH_USER")
    db_password: str = Field("postgres", alias="DWH_PASSWORD")

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # ── Storage ───────────────────────────────────────────────────────────────
    storage_backend: str = Field("minio", alias="STORAGE_BACKEND")
    s3_bucket: str = Field("lake", alias="S3_BUCKET")
    s3_endpoint: str | None = Field(None, alias="S3_ENDPOINT")
    aws_access_key_id: str | None = Field(None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("eu-north-1", alias="AWS_REGION")

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins_raw: str = Field(
        "http://localhost:8501,http://localhost:3000",
        alias="CORS_ORIGINS",
    )

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret_key: str = Field(
        "dev-secret-key-change-in-production", alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        15, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # ── Computed ──────────────────────────────────────────────────────────────
    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
