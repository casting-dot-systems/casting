from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import json
import os

from .env_manager import DotenvManager, EnvironmentContext, find_workspace_root


class LiveDiscordTestError(RuntimeError):
    """Raised when the live Discord testing environment is misconfigured."""


@dataclass(slots=True)
class LiveDiscordTestConfig:
    """Configuration required to run live Discord framework tests."""

    bot_token: str
    guild_id: str | None = None
    default_channel_id: str | None = None
    channel_aliases: dict[str, str] = field(default_factory=dict)
    dm_targets: dict[str, str] = field(default_factory=dict)
    ready_timeout: float = 20.0
    context: EnvironmentContext | None = None

    def resolve_channel(self, *, alias: str | None = None, channel_id: str | None = None) -> str:
        if channel_id:
            return channel_id
        if alias:
            target = self.channel_aliases.get(alias)
            if target:
                return target
            raise LiveDiscordTestError(f"Unknown channel alias: {alias}")
        if self.default_channel_id:
            return self.default_channel_id
        raise LiveDiscordTestError("A channel id or alias must be provided for live Discord tests")

    def resolve_dm_target(self, *, alias: str | None = None, user_id: str | None = None) -> str:
        if user_id:
            return user_id
        if alias:
            target = self.dm_targets.get(alias)
            if target:
                return target
            raise LiveDiscordTestError(f"Unknown DM target alias: {alias}")
        raise LiveDiscordTestError("A DM user id or alias is required for DM operations")


def load_live_test_config(
    *,
    env: Mapping[str, str] | None = None,
    dotenv_path: str | os.PathLike[str] | None = None,
) -> LiveDiscordTestConfig:
    workspace = find_workspace_root(Path(__file__))
    package_root = workspace / "libs" / "discord" / "framework"

    base_env = env if env is not None else os.environ
    manager = DotenvManager(base_env=base_env)
    manager.extend_with_defaults(workspace=workspace, package_root=package_root)

    custom_path: os.PathLike[str] | None = None
    if dotenv_path is None:
        location = base_env.get("DISCORD_TEST_DOTENV")
        if location:
            custom_path = os.fspath(location)
    else:
        custom_path = os.fspath(dotenv_path)
    if custom_path is not None:
        manager.add_layer(custom_path, name=str(custom_path), required=True)

    context = manager.load()

    token = context.get("DISCORD_TEST_BOT_TOKEN")
    if not token:
        raise LiveDiscordTestError("DISCORD_TEST_BOT_TOKEN is required for live Discord tests")

    default_channel = context.get("DISCORD_TEST_DEFAULT_CHANNEL")
    guild_id = context.get("DISCORD_TEST_GUILD_ID")
    ready_timeout = float(context.get("DISCORD_TEST_READY_TIMEOUT", "20"))

    channel_aliases = _parse_mapping(context.get("DISCORD_TEST_CHANNELS"))
    dm_targets = _parse_mapping(context.get("DISCORD_TEST_DM_TARGETS"))

    return LiveDiscordTestConfig(
        bot_token=token,
        guild_id=guild_id,
        default_channel_id=default_channel,
        channel_aliases=channel_aliases,
        dm_targets=dm_targets,
        ready_timeout=ready_timeout,
        context=context,
    )


def _parse_mapping(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    raw = raw.strip()
    if not raw:
        return {}
    if raw.startswith("{"):
        loaded = json.loads(raw)
        return {str(k): str(v) for k, v in loaded.items() if v is not None}
    result: dict[str, str] = {}
    for part in raw.split(","):
        if not part.strip():
            continue
        if "=" in part:
            key, value = part.split("=", 1)
        elif ":" in part:
            key, value = part.split(":", 1)
        else:
            raise LiveDiscordTestError(f"Invalid mapping entry: {part}")
        result[key.strip()] = value.strip()
    return result
