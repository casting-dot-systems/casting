import asyncio

from casting.platform.config import bootstrap_env, find_app_dir

from casting.discord.framework.discord_adapter import DiscordBotApp, DiscordConfig
from casting.discord.framework.discord_adapter.session_manager import SessionManager

from casting.apps.casting_query_bot.engine_bridge import DarcyEngineBridge

def _engine_factory(sessions: SessionManager) -> DarcyEngineBridge:
    return DarcyEngineBridge(sessions)


def _prepare_environment() -> None:
    package_root = find_app_dir(__file__)
    bootstrap_env(app_dir=package_root)


async def _run_async() -> None:
    config = DiscordConfig.from_env()
    bot = DiscordBotApp(config, engine_factory=_engine_factory)
    await bot.start()


def main() -> None:
    asyncio.run(_run_async())


def package_main() -> None:
    _prepare_environment()
    main()
