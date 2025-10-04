"""Cast maintenance scripts and registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List


@dataclass
class ScriptContext:
    """Execution context passed to scripts."""

    root: Path
    dry_run: bool = False


@dataclass
class ScriptResult:
    """Summary returned by scripts after execution."""

    updated_files: int = 0
    updated_config: bool = False
    removed_conflicts: bool = False
    notes: List[str] = field(default_factory=list)

    def summary_lines(self) -> List[str]:
        return list(self.notes)


@dataclass(frozen=True)
class RegisteredScript:
    slug: str
    description: str
    runner: Callable[[ScriptContext], ScriptResult]

    def run(self, ctx: ScriptContext) -> ScriptResult:
        return self.runner(ctx)


_SCRIPTS: Dict[str, RegisteredScript] = {}


def register(script: RegisteredScript) -> RegisteredScript:
    if script.slug in _SCRIPTS:
        raise ValueError(f"Duplicate script slug registered: {script.slug}")
    _SCRIPTS[script.slug] = script
    return script


def list_scripts() -> List[RegisteredScript]:
    return [s for _, s in sorted(_SCRIPTS.items(), key=lambda item: item[0])]


def get_script(slug: str) -> RegisteredScript | None:
    return _SCRIPTS.get(slug)


# Import bundled scripts so they register on module import.
from . import rename_identifiers  # noqa: E402  (import side-effect)

__all__ = [
    "ScriptContext",
    "ScriptResult",
    "RegisteredScript",
    "register",
    "list_scripts",
    "get_script",
]
