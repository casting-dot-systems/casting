"""Org-specific rule helpers built on top of core casting models."""

from __future__ import annotations

from casting.cast.core.models import CastConfig


def is_org_enabled(config: CastConfig) -> bool:
    """Return True when the provided cast configuration is active for the org."""

    return config.cast_name.startswith("Casting Systems")


__all__ = ["is_org_enabled"]
