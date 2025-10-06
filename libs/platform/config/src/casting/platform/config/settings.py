"""Shared typed settings helpers."""
from __future__ import annotations

from functools import cached_property
from typing import Any, ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .loader import DEFAULT_ENV


class SettingsBase(BaseSettings):
    """Base class for Casting settings models with sensible defaults."""

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_env: str = Field(default=DEFAULT_ENV, alias="APP_ENV")

    @cached_property
    def env(self) -> str:
        """Expose the effective app environment."""

        return self.app_env

    def describe(self) -> dict[str, Any]:
        """Return a redacted representation safe for logging."""

        return self.model_dump(mode="json", exclude_none=True, by_alias=True)


__all__ = ["SettingsBase"]
