.PHONY: up down logs py-ingest run-hour dq-hour bi-marts backfill-hours

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

dq-hour:
	docker compose exec -T streamlit python -m pipeline.cli.dq_hour --start "$(START)" --end "$(END)"

bi-marts:
	docker compose exec -T streamlit python -m pipeline.cli.build_bi_marts --days "$(DAYS)"

backfill-hours:
	docker compose exec -T streamlit python -m pipeline.cli.backfill_hours --start "$(START)" --end "$(END)"