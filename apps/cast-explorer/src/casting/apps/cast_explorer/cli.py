"""CLI interface for Cast Explorer."""

import typer
from rich.console import Console

app = typer.Typer(name="cast-explorer", help="CLI/TUI for exploring casts")
console = Console()


@app.command()
def explore():
    """Launch the cast explorer TUI."""
    console.print("🎭 Cast Explorer - TUI mode coming soon!")


@app.command()
def list():
    """List available casts."""
    console.print("📋 Listing casts...")


if __name__ == "__main__":
    app()