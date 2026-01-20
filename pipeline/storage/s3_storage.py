from __future__ import annotations

import boto3
from botocore.config import Config

from pipeline.config.settings import Settings
from pipeline.storage.storage import ObjectStorage


class S3Storage(ObjectStorage):
    def __init__(self, settings: Settings):
        self._bucket = settings.s3_bucket

        session = boto3.session.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )

        if settings.storage_backend == "minio":
            config = Config(s3={"addressing_style": "path"})
        else:
            config = None

        self._client = session.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            config=config,
        )

    def put_bytes(self, *, key, data, content_type):
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type
        )