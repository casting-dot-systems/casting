"""CLI interface for Prompt Generator."""

import typer
from rich.console import Console

app = typer.Typer(name="prompt-gen", help="AI prompt generation and management")
console = Console()


@app.command()
def generate():
    """Generate AI prompts for casting scenarios."""
    console.print("🤖 Generating prompts...")


@app.command()
def template():
    """Manage prompt templates."""
    console.print("📝 Managing prompt templates...")


if __name__ == "__main__":
    app()