from pathlib import Path
import os
import ruamel.yaml

from casting.apps.cast.tui import TerminalApp, TerminalContext
from casting.apps.cast.cli.tui_plugin import CastTUIPlugin

def _write_cast(root: Path):
    (root / ".cast").mkdir(parents=True, exist_ok=True)
    (root / "Cast").mkdir(parents=True, exist_ok=True)
    y = ruamel.yaml.YAML()
    y.dump(
        {"cast-version": 1, "cast-id": "00000000-0000-4000-8000-000000000000", "cast-name": "Smoke"},
        (root / ".cast" / "config.yaml").open("w", encoding="utf-8"),
    )

def test_plugin_registers_commands(tmp_path, monkeypatch):
    _write_cast(tmp_path)
    old = os.getcwd()
    os.chdir(tmp_path)  # so plugin's root discovery succeeds
    try:
        app = TerminalApp()
        ctx = TerminalContext(console=app.console, app=app)
        plugin = CastTUIPlugin()
        plugin.register(ctx)

        names = set(app._commands.keys())
        assert {"open", "edit", "sync", "report", "peers", "codebases", "cbsync"}.issubset(names)
    finally:
        os.chdir(old)