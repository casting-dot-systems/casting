
.PHONY: run dev fmt lint test alembic-init alembic-rev alembic-upgrade seed

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

fmt:
	black app tests
	isort app tests

lint:
	ruff check app tests

test:
	pytest -q

alembic-init:
	alembic init -t async alembic

alembic-rev:
	alembic revision --autogenerate -m "auto"

alembic-upgrade:
	alembic upgrade head

seed:
	python app/scripts/seed.py
