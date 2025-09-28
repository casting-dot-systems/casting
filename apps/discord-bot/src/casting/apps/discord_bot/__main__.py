from __future__ import annotations

import asyncio

from casting.discord.framework.discord_adapter import DiscordBotApp, DiscordConfig
from casting.discord.framework.discord_adapter.session_manager import SessionManager

from casting.apps.discord_bot.engine_bridge import DarcyEngineBridge


def _engine_factory(sessions: SessionManager) -> DarcyEngineBridge:
    return DarcyEngineBridge(sessions)


async def _run_async() -> None:
    config = DiscordConfig.from_env()
    bot = DiscordBotApp(config, engine_factory=_engine_factory)
    await bot.start()


def main() -> None:
    asyncio.run(_run_async())


if __name__ == "__main__":
    main()
