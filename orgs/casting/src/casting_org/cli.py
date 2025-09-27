"""CLI interface for the casting organization."""

import typer
from rich.console import Console

app = typer.Typer(name="casting-org", help="Organization-specific casting tools")
console = Console()


@app.command()
def dashboard():
    """Launch the organization dashboard."""
    console.print("📊 Organization Dashboard - Coming soon!")


@app.command()
def rules():
    """Manage organization-specific rules."""
    console.print("📋 Managing organization rules...")


if __name__ == "__main__":
    app()