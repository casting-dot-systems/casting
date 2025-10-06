"""Typed configuration for the Discord bot."""
from __future__ import annotations

from typing import Iterable

from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

from casting.platform.config import SettingsBase


def _split_csv(raw: str) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


class DiscordBotSettings(SettingsBase):
    """Environment-backed settings for the Discord bot."""

    api_url: str = Field(default="http://localhost:8000", alias="API_URL")
    markdown_folder_path: str = Field(default="./var/casts", alias="MARKDOWN_FOLDER_PATH")
    git_folder_path: str = Field(default="./var/git", alias="GIT_FOLDER_PATH")
    command_prefix: str = Field(default="/", alias="DISCORD_COMMAND_PREFIX")
    allowed_channels_raw: str = Field(default="", alias="DISCORD_ALLOWED_CHANNELS")
    allowed_roles_raw: str = Field(default="", alias="DISCORD_ALLOWED_ROLES")
    bot_token: SecretStr | None = Field(default=None, alias="DISCORD_TOKEN")
    bot_id: int | None = Field(default=None, alias="BOT_ID")

    model_config = SettingsConfigDict(env_nested_delimiter="__", extra="ignore")

    @property
    def allowed_channels(self) -> list[str]:
        return _split_csv(self.allowed_channels_raw)

    @property
    def allowed_roles(self) -> list[str]:
        return _split_csv(self.allowed_roles_raw)

    def require_token(self) -> str:
        if self.bot_token is None:
            raise ValueError("DISCORD_TOKEN is not configured")
        token = self.bot_token.get_secret_value()
        if not token:
            raise ValueError("DISCORD_TOKEN is empty")
        return token


__all__ = ["DiscordBotSettings"]
