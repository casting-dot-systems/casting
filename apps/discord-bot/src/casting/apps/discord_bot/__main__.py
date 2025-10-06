from __future__ import annotations

import asyncio
import os
from pathlib import Path

from casting.discord.framework.discord_adapter import DiscordBotApp, DiscordConfig
from casting.discord.framework.discord_adapter.session_manager import SessionManager
from casting.discord.framework.testing import DotenvManager, find_workspace_root

from casting.apps.discord_bot.engine_bridge import DarcyEngineBridge


def _engine_factory(sessions: SessionManager) -> DarcyEngineBridge:
    return DarcyEngineBridge(sessions)


def _locate_package_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return current.parent


def _prepare_environment() -> None:
    package_root = _locate_package_root()
    workspace_root = find_workspace_root(package_root)
    manager = DotenvManager()
    manager.extend_with_defaults(workspace=workspace_root, package_root=package_root)
    context = manager.load()
    os.environ.update(context.values)


async def _run_async() -> None:
    config = DiscordConfig.from_env()
    bot = DiscordBotApp(config, engine_factory=_engine_factory)
    await bot.start()


def main() -> None:
    _prepare_environment()
    print("=== Initial env snapshot ===")
    # Print just your suspect var (or all if you want)
    var_name = "BOT_TOKEN"
    print(f"{var_name}: {os.environ.get(var_name, 'NOT SET')}")
    asyncio.run(_run_async())


if __name__ == "__main__":
    main()
