from dagster import asset, Output, AssetExecutionContext, HourlyPartitionsDefinition
from datetime import datetime, timedelta, timezone

from pipeline.config.settings import Settings
from pipeline.storage.s3_storage import S3Storage
from pipeline.clients.usgs_client import USGSClient
from pipeline.jobs.ingest_raw_job import RawIngestionJob


hourly_partitions = HourlyPartitionsDefinition(start_date="2026-01-01-00:00")

@asset(
    partitions_def=hourly_partitions,
    key_prefix=["raw", "earthquake"],
    group_name="ingestion",
    description="Downloads raw GeoJSON from USGS API for a specific hour."
)
def raw_geojson(context: AssetExecutionContext):
    partition_date_str = context.partition_key
    
    window_start = datetime.strptime(partition_date_str, "%Y-%m-%d-%H:%M").replace(tzinfo=timezone.utc)
    window_end = window_start + timedelta(hours=1)
    
    context.log.info(f"Processing window: {window_start} -> {window_end}")

    settings = Settings.from_env()
    storage = S3Storage(settings)
    client = USGSClient()
    
    job = RawIngestionJob(settings=settings, storage=storage, client=client)

    s3_key = job.run(window_start=window_start, window_end=window_end)
    
    return Output(
        value=s3_key,
        metadata={
            "s3_path": f"s3://{settings.s3_bucket}/{s3_key}",
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
        }
    )