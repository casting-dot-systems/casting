from __future__ import annotations

from pathlib import Path

import pytest

from casting.discord.framework.testing.config import LiveDiscordTestConfig, load_live_test_config
from casting.discord.framework.testing.env_manager import DotenvManager, find_workspace_root


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_dotenv_manager_merges_layers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".git").mkdir()

    package_root = workspace / "libs" / "discord" / "framework"
    package_root.mkdir(parents=True)

    write(workspace / ".env", "A=1\nOVERRIDE=workspace\n")
    write(package_root / ".env", "OVERRIDE=package\nC=3\n")

    manager = DotenvManager(base_env={"OVERRIDE": "environment", "ENV_ONLY": "true"})
    manager.extend_with_defaults(workspace=workspace, package_root=package_root)
    monkeypatch.setenv("APP_ENV", "dev")
    context = manager.load()

    assert context.get("A") == "1"
    assert context.get("C") == "3"
    assert context.get("ENV_ONLY") == "true"
    assert context.get("OVERRIDE") == "environment"
    assert context.is_set("A") is True
    assert any(layer.path.name == ".env" and layer.name.startswith("workspace") for layer in context.loaded_layers)


def test_dotenv_manager_missing_required_layer(tmp_path: Path) -> None:
    manager = DotenvManager(base_env={})
    manager.add_layer(tmp_path / "missing.env", name="missing", required=True)
    with pytest.raises(FileNotFoundError):
        manager.load()


def test_find_workspace_root(tmp_path: Path) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()
    (workspace / ".git").mkdir()
    nested = workspace / "apps" / "service"
    nested.mkdir(parents=True)

    assert find_workspace_root(nested) == workspace


def test_load_live_test_config_uses_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()
    (workspace / ".git").mkdir()
    package_root = workspace / "libs" / "discord" / "framework"
    package_root.mkdir(parents=True)

    write(workspace / ".env", "DISCORD_TEST_BOT_TOKEN=workspace-token\nDISCORD_TEST_DEFAULT_CHANNEL=123\n")
    write(package_root / ".env", "DISCORD_TEST_CHANNELS=alias=456\n")

    monkeypatch.setattr(
        "casting.discord.framework.testing.config.find_workspace_root",
        lambda _start=None: workspace,
    )
    monkeypatch.setenv("APP_ENV", "dev")

    config = load_live_test_config(env={})
    assert isinstance(config, LiveDiscordTestConfig)
    assert config.bot_token == "workspace-token"
    assert config.default_channel_id == "123"
    assert config.channel_aliases == {"alias": "456"}
    assert config.context is not None
    assert any(layer.path == workspace / ".env" for layer in config.context.loaded_layers)
