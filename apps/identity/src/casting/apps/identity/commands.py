"""CLI commands for identity management."""

from __future__ import annotations

import json
from typing import Optional

import typer

from casting.identity import (
    ensure_identity_table,
    get_member_from_discord_id,
    get_member_from_identity,
    get_member_from_notion_id,
    get_member_from_work_email,
    list_identities,
    set_identity,
)

from .config import get_engine_from_cli


def init_db_command(
    db: Optional[str] = typer.Option(
        None, help="Database URL (overrides DATABASE_URL env var)."
    )
) -> None:
    """Create schema and table for application.identity if not present."""
    engine = get_engine_from_cli(db)
    with engine.begin() as conn:
        ensure_identity_table(conn)
    typer.echo("✅ application.identity initialized (idempotent).")


def add_identity_command(
    member_id: str = typer.Option(..., help="Target member_id (UUID) in catalog.members."),
    identity_type: str = typer.Option(..., "--type", "-t", help="Identity type, e.g. discord|notion|work_email|..."),
    value: str = typer.Option(..., "--value", "-v", help="Identity value to map."),
    db: Optional[str] = typer.Option(None, help="Database URL (overrides env)."),
) -> None:
    """Add or update an identity mapping (upsert)."""
    engine = get_engine_from_cli(db)
    with engine.begin() as conn:
        set_identity(conn, member_id=member_id, identity_type=identity_type, identity_value=value)
    typer.echo(f"✅ Upserted identity [{identity_type}={value}] -> member {member_id}.")


def list_identities_command(
    member_id: Optional[str] = typer.Option(None, help="Filter by member_id."),
    db: Optional[str] = typer.Option(None, help="Database URL (overrides env)."),
) -> None:
    """List identities (optionally for a specific member)."""
    engine = get_engine_from_cli(db)
    with engine.begin() as conn:
        rows = list_identities(conn, member_id=member_id)

    if not rows:
        typer.echo("No identities found.")
        return

    # Compact table-like output
    header = ("identity_id", "member_id", "identity_type", "identity_value", "created_at", "updated_at")
    widths = [max(len(str(row.get(col, ""))) for row in rows + [dict(zip(header, header))]) for col in header]
    line = " | ".join(col.ljust(w) for col, w in zip(header, widths))
    typer.echo(line)
    typer.echo("-" * len(line))
    for r in rows:
        typer.echo(" | ".join(str(r.get(col, "")).ljust(w) for col, w in zip(header, widths)))


def find_member_command(
    identity_type: str = typer.Option(..., "--type", "-t", help="Identity type (discord|notion|work_email|...)."),
    value: str = typer.Option(..., "--value", "-v", help="Identity value."),
    db: Optional[str] = typer.Option(None, help="Database URL (overrides env)."),
    no_fallback: bool = typer.Option(False, help="Disable fallback to members.primary_email for work_email."),
) -> None:
    """
    Resolve and print a member by identity. Always returns:
    {
      "member": {...},
      "identities": [{"identity_type": "...", "identity_value": "..."}, ...]
    }
    """
    engine = get_engine_from_cli(db)
    with engine.begin() as conn:
        if identity_type == "discord":
            result = get_member_from_discord_id(conn, value)
        elif identity_type == "notion":
            result = get_member_from_notion_id(conn, value)
        elif identity_type == "work_email":
            result = get_member_from_work_email(conn, value, fallback_to_members_email=not no_fallback)
        else:
            result = get_member_from_identity(conn, identity_type, value)

    if not result:
        typer.echo("No matching member found.")
        raise typer.Exit(code=1)

    # Pretty JSON for ergonomics
    typer.echo(json.dumps(result, indent=2, default=str))