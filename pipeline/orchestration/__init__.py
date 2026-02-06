from dagster import Definitions, load_assets_from_modules

from pipeline.orchestration.assets import ingestion, silver, warehouse, analytics


ingestion_assets = load_assets_from_modules([ingestion])
silver_assets = load_assets_from_modules([silver])
ods_assets = load_assets_from_modules([warehouse])
gold_assets = load_assets_from_modules([analytics])

defs = Definitions(
    assets=[*ingestion_assets, *silver_assets, *ods_assets, *gold_assets],
)