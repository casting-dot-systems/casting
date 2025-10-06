from __future__ import annotations

from pathlib import Path

import pytest

from casting.discord.framework.testing.config import LiveDiscordTestConfig, load_live_test_config
from casting.discord.framework.testing.env_manager import DotenvManager, find_workspace_root


def test_dotenv_manager_merges_layers(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".git").mkdir()

    package_root = workspace / "libs" / "discord" / "framework"
    package_root.mkdir(parents=True)

    (workspace / ".env").write_text("A=1\nOVERRIDE=workspace\n")
    (workspace / ".env.local").write_text("B=2\n")
    (package_root / ".env").write_text("C=3\n")
    (package_root / ".env.local").write_text("OVERRIDE=package\n")

    manager = DotenvManager(base_env={"OVERRIDE": "environment", "ENV_ONLY": "true"})
    manager.extend_with_defaults(workspace=workspace, package_root=package_root)
    context = manager.load()

    assert context.get("A") == "1"
    assert context.get("B") == "2"
    assert context.get("C") == "3"
    assert context.get("ENV_ONLY") == "true"
    # Environment variables take precedence over dotenv files
    assert context.get("OVERRIDE") == "environment"
    assert context.is_set("A") is True


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


def test_load_live_test_config_uses_layered_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()
    (workspace / ".git").mkdir()
    package_root = workspace / "libs" / "discord" / "framework"
    package_root.mkdir(parents=True)

    (workspace / ".env").write_text("DISCORD_TEST_BOT_TOKEN=workspace-token\nDISCORD_TEST_DEFAULT_CHANNEL=123\n")
    (package_root / ".env").write_text("DISCORD_TEST_CHANNELS=alias=456\n")

    monkeypatch.setattr(
        "casting.discord.framework.testing.config.find_workspace_root",
        lambda _start=None: workspace,
    )

    config = load_live_test_config(env={})
    assert isinstance(config, LiveDiscordTestConfig)
    assert config.bot_token == "workspace-token"
    assert config.default_channel_id == "123"
    assert config.channel_aliases == {"alias": "456"}
    assert config.context is not None
    assert any(layer.path == workspace / ".env" for layer in config.context.loaded_layers)
