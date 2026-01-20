from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str
    storage_backend: str  # "minio" | "aws"

    s3_bucket: str
    s3_endpoint: str | None
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    aws_region: str

    # Filters
    min_mag: float

    @staticmethod
    def from_env() -> Settings:
        app_env = os.getenv("APP_ENV", "dev")
        storage_backend = os.getenv("STORAGE_BACKEND", "minio")

        s3_bucket = os.getenv("S3_BUCKET", "lake")
        s3_endpoint = os.getenv("S3_ENDPOINT") or None
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID") or None
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY") or None
        aws_region = os.getenv("AWS_REGION", "eu-north-1")

        min_mag = float(os.getenv("MIN_MAG", "2.5"))

        return Settings(
            app_env=app_env,
            storage_backend=storage_backend,
            s3_bucket=s3_bucket,
            s3_endpoint=s3_endpoint,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_region=aws_region,
            min_mag=min_mag,
        )