"""Main CLI application setup."""

from __future__ import annotations

import typer

from .commands import (
    add_identity_command,
    find_member_command,
    init_db_command,
    list_identities_command,
)


def create_app() -> typer.Typer:
    """Create and configure the main CLI application."""
    app = typer.Typer(add_completion=False, help="Identity management UI for casting systems.")

    app.command("init-db")(init_db_command)
    app.command("add")(add_identity_command)
    app.command("list")(list_identities_command)
    app.command("find")(find_member_command)

    return app