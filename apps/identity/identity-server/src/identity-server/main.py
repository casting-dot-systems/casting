
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app.api.routers import members, meetings, projects, identities, resolve

# Create tables (for dev/local) — in production use Alembic migrations
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cast-Identity", version="0.1.0", docs_url="/docs", redoc_url="/redoc")

# Allow local tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# Routers
app.include_router(members.router)
app.include_router(meetings.router)
app.include_router(projects.router)
app.include_router(identities.router)
app.include_router(resolve.router)
