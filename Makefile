.PHONY: up down logs py-ingest run-hour

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f

py-ingest:
	docker compose exec -T streamlit python -m pipeline.cli.ingest_raw --start "$(START)" --end "$(END)"

run-hour:
	docker compose exec -T streamlit python -m pipeline.cli.run_hour --start "$(START)" --end "$(END)"