from dagster import asset, Output, AssetExecutionContext, AssetIn
from datetime import datetime, timedelta, timezone

from pipeline.config.pg_settings import PostgresSettings
from pipeline.config.settings import Settings
from pipeline.storage.s3_storage import S3Storage
from pipeline.warehouse.pg import PostgresRepository
from pipeline.jobs.load_from_silver_job import LoadFromSilverJob
from pipeline.orchestration.assets.ingestion import hourly_partitions

@asset(
    partitions_def=hourly_partitions,
    key_prefix=["ods", "earthquake"],
    group_name="ods",
    description="Loads data from Silver Parquet to Postgres ODS table.",
    ins={"silver_key": AssetIn(key=["silver", "earthquake", "silver_events"])}
)
def ods_events(context: AssetExecutionContext, silver_key: str):
    partition_date_str = context.partition_key
    window_start = datetime.strptime(partition_date_str, "%Y-%m-%d-%H:%M").replace(tzinfo=timezone.utc)
    window_end = window_start + timedelta(hours=1)

    settings = Settings.from_env()
    storage = S3Storage(settings)
    pg_settings = PostgresSettings.from_env()
    repo = PostgresRepository(pg_settings)
    
    silver_bytes = storage.get_bytes(key=silver_key)
    
    job = LoadFromSilverJob(repo=repo, storage=storage)
    count = job.run(silver_parquet=silver_bytes)
    
    return Output(
        value=count,
        metadata={
            "rows_inserted": count,
            "source_silver": silver_key,
            "table": "ods.fct_earthquake_event"
        }
    )