from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import os

from casting.platform.config.loader import merge_env_dicts
from dotenv import dotenv_values

@dataclass(slots=True)
class DotenvLayer:
    name: str
    path: Path
    required: bool = False


@dataclass(slots=True)
class EnvironmentContext:
    values: dict[str, str]
    loaded_layers: list[DotenvLayer]

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.values.get(key, default)

    def require(self, *keys: str) -> None:
        missing = [key for key in keys if not self.values.get(key)]
        if missing:
            raise KeyError(f"Missing required environment variables: {', '.join(missing)}")

    def is_set(self, key: str) -> bool:
        value = self.values.get(key)
        return value is not None and value != ""


class DotenvManager:
    """Layered dotenv loader suitable for monorepo environments."""

    def __init__(self, *, base_env: Mapping[str, str] | None = None) -> None:
        if base_env is None:
            base_env = os.environ
        self._base_env = dict(base_env)
        self._layers: list[DotenvLayer] = []
        self._seen_paths: set[Path] = set()
        self._workspace: Path | None = None
        self._package_root: Path | None = None
        self._env: str | None = None

    def add_layer(self, path: str | os.PathLike[str], *, name: str | None = None, required: bool = False) -> None:
        path_obj = Path(path).expanduser()
        if name is None:
            name = path_obj.name
        if path_obj in self._seen_paths:
            return
        self._layers.append(DotenvLayer(name=name, path=path_obj, required=required))
        self._seen_paths.add(path_obj)

    def extend_with_defaults(self, *, workspace: Path, package_root: Path | None = None) -> None:
        self._workspace = workspace
        self._package_root = package_root
        self.add_layer(workspace / ".env", name="workspace .env")
        if package_root is not None:
            self.add_layer(package_root / ".env", name=f"{package_root.name} .env")

    def load(self) -> EnvironmentContext:
        for layer in self._layers:
            if layer.required and not layer.path.exists():
                raise FileNotFoundError(f"Required dotenv layer '{layer.name}' not found at {layer.path}")

        data_dicts: list[dict[str, str | None]] = []
        loaded_layers: list[DotenvLayer] = []
        for layer in self._layers:
            path = layer.path
            if not path.exists():
                if layer.required:
                    raise FileNotFoundError(f"Required dotenv layer '{layer.name}' not found at {layer.path}")
                continue
            data_dicts.append(dotenv_values(path))
            loaded_layers.append(DotenvLayer(name=layer.name, path=path))

        merged = merge_env_dicts(data_dicts, existing=self._base_env)
        return EnvironmentContext(values=merged, loaded_layers=loaded_layers)

    def set_env(self, env: str | None) -> None:
        self._env = env


def find_workspace_root(start: Path | None = None) -> Path:
    current = Path(start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError("Unable to locate workspace root (.git directory not found)")
