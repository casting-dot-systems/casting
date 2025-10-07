"""Entrypoint delegating to the shared Discord bot."""
from __future__ import annotations

from casting.platform.config import bootstrap_env, find_app_dir
from casting.apps.casting_query_bot.__main__ import main as upstream_main

def main() -> None:
    """Launch the shared Discord bot with org-specific overrides."""
    APP_DIR = find_app_dir(__file__)
    bootstrap_env(app_dir=APP_DIR)
    upstream_main()


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
