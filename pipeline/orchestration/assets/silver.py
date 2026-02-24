from datetime import datetime, timedelta, timezone

from dagster import AssetExecutionContext, AssetIn, Output, asset

from pipeline.config.settings import Settings
from pipeline.jobs.write_silver_job import SilverWriteJob
from pipeline.orchestration.assets.ingestion import hourly_partitions
from pipeline.storage.s3_storage import S3Storage


@asset(
    partitions_def=hourly_partitions,
    key_prefix=["silver", "earthquake"],
    group_name="silver",
    description="Parses GeoJSON and saves enriched Parquet to Silver layer.",
    ins={"raw_key": AssetIn(key=["raw", "earthquake", "raw_geojson"])}
)
def silver_events(context: AssetExecutionContext, raw_key: str):
    
    partition_date_str = context.partition_key
    window_start = datetime.strptime(partition_date_str, "%Y-%m-%d-%H:%M").replace(tzinfo=timezone.utc)
    window_end = window_start + timedelta(hours=1)

    settings = Settings.from_env()
    storage = S3Storage(settings)
    
    raw_bytes = storage.get_bytes(key=raw_key)
    
    job = SilverWriteJob(storage=storage)
    silver_key = job.run(raw_geojson=raw_bytes, window_start=window_start, window_end=window_end)
    
    return Output(
        value=silver_key,
        metadata={
            "s3_path": f"s3://{settings.s3_bucket}/{silver_key}",
            "source_raw": raw_key
        }
    )