
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from identity_server.api.routers import identities, resolve

# Note: Table creation is handled by Alembic migrations.
# The ApplicationIdentity table goes in public schema.
# Entity tables (Member, Meeting, Project) exist in catalog schema and are managed externally.

app = FastAPI(
    title="Cast-Identity",
    version="0.1.0",
    description="Identity resolution service for Cast entities",
    docs_url="/docs",
    redoc_url="/redoc"
)

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


# Routers - only identity management and resolution
app.include_router(identities.router)
app.include_router(resolve.router)
