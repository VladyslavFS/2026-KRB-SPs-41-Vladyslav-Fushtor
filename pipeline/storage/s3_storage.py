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

    def put_bytes(self, *, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type
        )

    def get_bytes(self, *, key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    def upload_file(self, *, local_path: str, key: str, content_type: str | None = None) -> None:
        extra_args = dict()
        if content_type:
            extra_args["ContentType"] = content_type
        if extra_args:
            self._client.upload_file(local_path, self._bucket, key, ExtraArgs=extra_args)
        else:
            self._client.upload_file(local_path, self._bucket, key)

    def download_file(self, *, key: str, local_path: str) -> None:
        self._client.download_file(self._bucket , key, local_path)

    def list_keys(self, *, prefix: str) -> list[str]:
        paginator = self._client.get_paginator("list_objects_v2")
        keys = []
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            if "Contents" in page:
                for obj in page["Contents"]:
                    keys.append(obj["Key"])
        return keys