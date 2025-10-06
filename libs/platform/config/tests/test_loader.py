from __future__ import annotations

import os
from pathlib import Path

import pytest

from casting.platform.config.loader import EnvLoader, apply_env, bootstrap_env, find_app_dir


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_loader_reads_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    write(app_dir / ".env", "TOKEN=dev\nEXTRA=value\n")

    monkeypatch.delenv("TOKEN", raising=False)
    loader = EnvLoader(app_dir)
    result = loader.load()

    assert result.enabled is True
    assert result.file == app_dir / ".env"
    assert result.values["TOKEN"] == "dev"
    assert result.values["EXTRA"] == "value"


def test_loader_skips_in_production(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    write(app_dir / ".env", "TOKEN=dev\n")

    monkeypatch.setenv("APP_ENV", "prod")
    loader = EnvLoader(app_dir)
    result = loader.load()

    assert result.enabled is False
    assert result.file is None
    assert "TOKEN" not in result.values


def test_loader_handles_missing_file(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    app_dir.mkdir()

    loader = EnvLoader(app_dir)
    result = loader.load()

    assert result.enabled is True
    assert result.file is None


def test_existing_environment_variable_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    write(app_dir / ".env", "TOKEN=file\n")

    monkeypatch.setenv("TOKEN", "env")
    loader = EnvLoader(app_dir)
    result = loader.load()

    assert result.values["TOKEN"] == "env"


def test_bootstrap_env_applies_loaded_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    write(app_dir / ".env", "VALUE=from-file\n")

    monkeypatch.delenv("VALUE", raising=False)
    result = bootstrap_env(app_dir=app_dir, verbose=False)

    assert os.environ["VALUE"] == "from-file"
    assert result.file == app_dir / ".env"


def test_apply_env_does_not_override_existing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOKEN", "env")
    applied = apply_env({"TOKEN": "file", "NEW": "value"})

    assert os.environ["TOKEN"] == "env"
    assert os.environ["NEW"] == "value"
    assert applied == ["NEW"]


def test_find_app_dir_prefers_env_file(tmp_path: Path) -> None:
    nested = tmp_path / "repo" / "apps" / "service" / "src"
    nested.mkdir(parents=True)
    write(tmp_path / "repo" / "apps" / "service" / ".env", "KEY=value\n")

    discovered = find_app_dir(nested / "module.py")
    assert discovered == tmp_path / "repo" / "apps" / "service"


def test_find_app_dir_falls_back_to_pyproject(tmp_path: Path) -> None:
    nested = tmp_path / "workspace" / "pkg" / "src"
    nested.mkdir(parents=True)
    write(tmp_path / "workspace" / "pkg" / "pyproject.toml", "[project]\nname='pkg'\n")

    discovered = find_app_dir(nested / "module.py")
    assert discovered == tmp_path / "workspace" / "pkg"
