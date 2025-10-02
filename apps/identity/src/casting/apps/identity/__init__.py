"""Identity management CLI application."""

from .cli import create_app


def main() -> None:
    """Main entry point for the CLI application."""
    app = create_app()
    app()


if __name__ == "__main__":
    main()