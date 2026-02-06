from dagster import Definitions, load_assets_from_modules

from pipeline.orchestration.assets import ingestion, silver


ingestion_assets = load_assets_from_modules([ingestion])
silver_assets = load_assets_from_modules([silver])

defs = Definitions(
    assets=[*ingestion_assets, *silver_assets],
)