from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import os

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

    def add_layer(self, path: str | os.PathLike[str], *, name: str | None = None, required: bool = False) -> None:
        path_obj = Path(path).expanduser()
        if name is None:
            name = path_obj.name
        if path_obj in self._seen_paths:
            return
        self._layers.append(DotenvLayer(name=name, path=path_obj, required=required))
        self._seen_paths.add(path_obj)

    def extend_with_defaults(self, *, workspace: Path, package_root: Path | None = None) -> None:
        self.add_layer(workspace / ".env", name="workspace .env")
        self.add_layer(workspace / ".env.local", name="workspace .env.local")
        self.add_layer(workspace / ".env.test", name="workspace .env.test")
        if package_root is not None:
            self.add_layer(package_root / ".env", name=f"{package_root.name} .env")
            self.add_layer(package_root / ".env.local", name=f"{package_root.name} .env.local")
            self.add_layer(package_root / ".env.test", name=f"{package_root.name} .env.test")

    def load(self) -> EnvironmentContext:
        merged: dict[str, str] = {}
        loaded_layers: list[DotenvLayer] = []
        for layer in self._layers:
            if layer.path.is_file():
                data = dotenv_values(layer.path)
                merged.update({key: value for key, value in data.items() if value is not None})
                loaded_layers.append(layer)
            elif layer.required:
                raise FileNotFoundError(f"Required dotenv layer '{layer.name}' not found at {layer.path}")
        merged.update(self._base_env)
        return EnvironmentContext(values=merged, loaded_layers=loaded_layers)


def find_workspace_root(start: Path | None = None) -> Path:
    current = Path(start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError("Unable to locate workspace root (.git directory not found)")

