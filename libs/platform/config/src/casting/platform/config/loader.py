"""Minimal development environment loader for a single `.env` file."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
import os

from dotenv import dotenv_values


DEFAULT_ENV = "dev"
DEFAULT_PROD_ENVS = {"prod", "production", "staging"}


@dataclass(frozen=True, slots=True)
class EnvLoadResult:
    """Resolved environment data for an application."""

    values: dict[str, str]
    file: Path | None
    effective_env: str
    enabled: bool


class EnvLoader:
    """Load an app-specific `.env` file for development/test use."""

    def __init__(
        self,
        app_dir: Path,
        *,
        filename: str | os.PathLike[str] = ".env",
        disable_in_prod: bool = True,
        prod_env_names: Iterable[str] | None = None,
        env: str | None = None,
        base_env: Mapping[str, str] | None = None,
    ) -> None:
        self.app_dir = Path(app_dir).resolve()
        self._requested_env = env
        self.base_env = dict(base_env) if base_env is not None else dict(os.environ)
        self.disable_in_prod = disable_in_prod
        self.prod_env_names = {name.lower() for name in (prod_env_names or DEFAULT_PROD_ENVS)}

        filename_path = Path(filename)
        if not filename_path.is_absolute():
            filename_path = self.app_dir / filename_path
        self.env_path = filename_path

    @property
    def env(self) -> str:
        if self._requested_env is not None:
            return self._requested_env
        return self.base_env.get("APP_ENV", DEFAULT_ENV)

    def _should_skip(self) -> bool:
        if not self.disable_in_prod:
            return False
        return self.env.lower() in self.prod_env_names

    def load(self) -> EnvLoadResult:
        if self._should_skip():
            return EnvLoadResult(
                values=dict(self.base_env),
                file=None,
                effective_env=self.env,
                enabled=False,
            )

        if not self.env_path.is_file():
            return EnvLoadResult(
                values=dict(self.base_env),
                file=None,
                effective_env=self.env,
                enabled=True,
            )

        merged = merge_env_dicts((dotenv_values(self.env_path),), existing=self.base_env)
        return EnvLoadResult(
            values=merged,
            file=self.env_path,
            effective_env=self.env,
            enabled=True,
        )


def merge_env_dicts(dicts: Iterable[dict[str, str | None]], *, existing: dict[str, str]) -> dict[str, str]:
    """Merge dotenv dictionaries without overriding explicit environment variables."""

    merged: dict[str, str] = {}
    for data in dicts:
        for key, value in data.items():
            if key in existing or value is None:
                continue
            merged[key] = value
    merged.update(existing)
    return merged


def find_app_dir(start: str | os.PathLike[str] | None = None, *, marker: str = ".env") -> Path:
    """Locate the application directory by walking up from ``start``.

    Preference order: directory containing ``marker`` (defaults to ``.env``), falling
    back to the nearest ancestor with a ``pyproject.toml``. Raises ``RuntimeError`` if
    neither marker is found.
    """

    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent

    fallback: Path | None = None
    for directory in [current, *current.parents]:
        if marker and (directory / marker).exists():
            return directory
        if fallback is None and (directory / "pyproject.toml").exists():
            fallback = directory

    if fallback is not None:
        return fallback
    raise RuntimeError(
        f"Unable to locate application directory starting at {current};"
        " no '.env' or 'pyproject.toml' markers found."
    )


def load_layers(
    app_dir: Path,
    *,
    filename: str | os.PathLike[str] = ".env",
    disable_in_prod: bool = True,
    prod_env_names: Iterable[str] | None = None,
    env: str | None = None,
) -> dict[str, str]:
    """Return merged environment variables for an app directory."""

    loader = EnvLoader(
        Path(app_dir),
        filename=filename,
        disable_in_prod=disable_in_prod,
        prod_env_names=prod_env_names,
        env=env,
    )
    return loader.load().values


def apply_env(envmap: dict[str, str]) -> list[str]:
    """Apply values into ``os.environ`` without clobbering existing keys."""

    applied: list[str] = []
    for key, value in envmap.items():
        if key in os.environ:
            continue
        os.environ[key] = value
        applied.append(key)
    return applied


def bootstrap_env(
    *,
    app_dir: Path,
    filename: str | os.PathLike[str] = ".env",
    disable_in_prod: bool = True,
    prod_env_names: Iterable[str] | None = None,
    env: str | None = None,
    verbose: bool | None = None,
    base_env: Mapping[str, str] | None = None,
) -> EnvLoadResult:
    """Load a development `.env` file for an app and apply it."""

    loader = EnvLoader(
        Path(app_dir),
        filename=filename,
        disable_in_prod=disable_in_prod,
        prod_env_names=prod_env_names,
        env=env,
        base_env=base_env,
    )
    result = loader.load()
    applied = apply_env(result.values)

    if verbose:
        status = "loaded" if result.enabled and result.file is not None else "skipped"
        source = result.file.name if result.file is not None else "no file"
        print(
            f"[env] {status} {len(applied)} variables for APP_ENV={result.effective_env} from: {source}"
        )
    return result


__all__ = [
    "EnvLoadResult",
    "EnvLoader",
    "apply_env",
    "bootstrap_env",
    "find_app_dir",
    "load_layers",
    "merge_env_dicts",
]
