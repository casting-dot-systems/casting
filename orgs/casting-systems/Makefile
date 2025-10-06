dev:
	uv sync --locked --group dev --group migrate --group pipeline

test:
	uv run pytest -q

migrate-up:
	uv run alembic -c migrations/agent_hub/alembic.ini upgrade head

migrate-down:
	uv run alembic -c migrations/agent_hub/alembic.ini downgrade -1

dbt-build:
	uv run dbt build --profiles-dir sql

discord-bot:
	uv run --project apps/discord-bot casting-org-discord-bot
