.PHONY: up down logs py-ingest minio-init

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f

py-ingest:
	docker compose exec -T streamlit python -m pipeline.cli.ingest_raw --start "$(START)" --end "$(END)"