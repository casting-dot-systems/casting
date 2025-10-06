dev:
	uv sync --locked --group dev --group migrate --group pipeline

test:
	uv run poe test

lint:
	uv run poe lint

types:
	uv run poe check

migrate-up:
	uv run alembic -c orgs/casting-systems/migrations/agent_hub/alembic.ini upgrade head

migrate-down:
	uv run alembic -c orgs/casting-systems/migrations/agent_hub/alembic.ini downgrade -1

dbt-build:
	uv run dbt build --profiles-dir orgs/casting-systems/sql
