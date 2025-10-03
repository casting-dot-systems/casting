
# Cast-Identity

A FastAPI service that resolves "true" entities (members, meetings, projects, etc.) to their identities across applications (email, Notion, Obsidian, Discord, ...). It also exposes full CRUD for entities and application identities.

> **Auth**: none (local-only for now).  
> **DB**: SQLAlchemy ORM. SQLite by default; Postgres supported.

---

## Quickstart (SQLite)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
# Open http://127.0.0.1:8000/docs
```

## Quickstart (Docker + Postgres)

```bash
docker compose up --build
# API -> http://127.0.0.1:8000/docs
```

## Environment

Copy `.env.example` to `.env` (optional). Env vars:
- `DATABASE_URL` — default: `sqlite:///./cast_identity.db`
- `APP_HOST` — default: `0.0.0.0`
- `APP_PORT` — default: `8000`
- `LOG_LEVEL` — default: `info`

## Data Model (simplified)

```
members(id, full_name, primary_email, created_at, updated_at)
meetings(id, title, scheduled_start, scheduled_end, created_at, updated_at)
projects(id, name, description, created_at, updated_at)

application_identities(
  id, entity_type, entity_id, application, external_id, display_name, uri, metadata, is_primary,
  created_at, updated_at,
  UNIQUE(entity_type, entity_id, application)
)
```

- `entity_type` is a string (`member`, `meeting`, `project`, ...)
- `application` is a string (`email`, `notion`, `obsidian`, `discord`, ...)
- `external_id` is the application's identifier (email, page ID, channel/user ID, etc.)
- `metadata` is arbitrary JSON for app-specific extras

## API Overview

- `GET /health`
- CRUD:
  - Members: `/members`
  - Meetings: `/meetings`
  - Projects: `/projects`
  - Application Identities: `/identities` (filter by `entity_type` & `entity_id`)
- Resolver:
  - `GET /resolve/{entity_type}/{entity_id}` → returns the **true entity** and all of its **application identities**

OpenAPI docs: `/docs`

## Development

- Format: `make fmt`
- Lint: `make lint`
- Test: `make test`
- Migrations (Alembic): `make alembic-rev && make alembic-upgrade`

## Seeding

```bash
python app/scripts/seed.py
```

This creates sample member/project/meeting with a few identities for local testing.

## Notes

- This project uses **SQLAlchemy 2.x** (synchronous engine) and **Pydantic v2**.
- `application_identities` uses `(entity_type, entity_id)` to support multiple true-tables without fragile cross-table FKs.
- Extend by adding more entity tables and reusing the identities pattern.
```