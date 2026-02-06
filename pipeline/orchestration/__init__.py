from dagster import Definitions, load_assets_from_modules, build_schedule_from_partitioned_job, define_asset_job
from pipeline.orchestration.assets import ingestion, silver, warehouse, analytics, quality

ingestion_assets = load_assets_from_modules([ingestion])
silver_assets = load_assets_from_modules([silver])
ods_assets = load_assets_from_modules([warehouse])
gold_assets = load_assets_from_modules([analytics])
quality_assets = load_assets_from_modules([quality])

all_assets = [*ingestion_assets, *silver_assets, *ods_assets, *gold_assets, *quality_assets]

earthquake_job = define_asset_job(
    name="earthquake_pipeline_job",
    selection=all_assets
)

earthquake_schedule = build_schedule_from_partitioned_job(
    job=earthquake_job,
    name="earthquake_hourly_schedule",
)

defs = Definitions(
    assets=all_assets,
    jobs=[earthquake_job],
    schedules=[earthquake_schedule],
)