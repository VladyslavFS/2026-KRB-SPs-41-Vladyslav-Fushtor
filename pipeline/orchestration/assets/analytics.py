from dagster import asset, Output, AssetExecutionContext, AssetIn

from pipeline.config.settings import Settings
from pipeline.config.pg_settings import PostgresSettings
from pipeline.storage.s3_storage import S3Storage
from pipeline.warehouse.pg import PostgresRepository

from pipeline.jobs.build_gold_job import BuildGoldJob
from pipeline.jobs.load_bi_to_serving_layer_job import LoadBIStoreJob
from pipeline.orchestration.assets.ingestion import hourly_partitions


@asset(
    partitions_def=hourly_partitions,
    key_prefix=["gold", "earthquake"],
    group_name="gold",
    description="Builds Gold Layer (Daily Aggregates) in S3.",
    ins={"ods_trigger": AssetIn(key=["ods", "earthquake", "ods_events"])}
)
def gold_events(context: AssetExecutionContext, ods_trigger: int):
    days_to_process = 30
    
    settings = Settings.from_env()
    storage = S3Storage(settings)
    pg_settings = PostgresSettings.from_env()
    repo = PostgresRepository(pg_settings)
    
    job = BuildGoldJob(repo=repo, storage=storage, bucket=settings.s3_bucket)
    result_keys = job.run(days=days_to_process)
    
    return Output(
        value=result_keys, # Список створених файлів
        metadata={
            "files_generated": len(result_keys),
            "days_processed": days_to_process
        }
    )

@asset(
    partitions_def=hourly_partitions,
    key_prefix=["bi", "earthquake"],
    group_name="bi",
    description="Syncs Gold S3 data to Postgres BI tables.",
    ins={"gold_files": AssetIn(key=["gold", "earthquake", "gold_events"])}
)
def bi_tables(context: AssetExecutionContext, gold_files: list):
    days_to_sync = 30
    
    settings = Settings.from_env()
    storage = S3Storage(settings)
    pg_settings = PostgresSettings.from_env()
    repo = PostgresRepository(pg_settings)
    
    job = LoadBIStoreJob(repo=repo, storage=storage, bucket=settings.s3_bucket)
    job.run(days=days_to_sync)
    
    return Output(
        value="Synced",
        metadata={
            "status": "Success",
            "source_gold_files": len(gold_files)
        }
    )