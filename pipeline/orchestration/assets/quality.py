from dagster import asset, Output, AssetExecutionContext, AssetIn
from datetime import datetime, timedelta, timezone

from pipeline.config.pg_settings import PostgresSettings
from pipeline.warehouse.pg import PostgresRepository
from pipeline.jobs.dq_job import DataQualityJob
from pipeline.orchestration.assets.ingestion import hourly_partitions

@asset(
    partitions_def=hourly_partitions,
    key_prefix=["dq", "earthquake"],
    group_name="quality",
    description="Runs data quality checks on ODS data.",
    ins={"ods_trigger": AssetIn(key=["ods", "earthquake", "ods_events"])}
)
def dq_report(context: AssetExecutionContext, ods_trigger: int):
    partition_date_str = context.partition_key
    window_start = datetime.strptime(partition_date_str, "%Y-%m-%d-%H:%M").replace(tzinfo=timezone.utc)
    window_end = window_start + timedelta(hours=1)

    pg_settings = PostgresSettings.from_env()
    repo = PostgresRepository(pg_settings)

    job = DataQualityJob(repo=repo)
    
    issues_count = job.run(window_start=window_start, window_end=window_end)
    
    status = "SUCCESS" if issues_count == 0 else "WARNING"
    
    return Output(
        value=issues_count,
        metadata={
            "dq_status": status,
            "issues_found": issues_count,
            "report_table": "dq.dq_run"
        }
    )