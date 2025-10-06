"""Script to rename legacy cast identifiers and remove version metadata."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List

from ruamel.yaml import YAML

from casting.cast.core.yamlio import parse_cast_file, write_cast_file
from . import RegisteredScript, ScriptContext, ScriptResult, register


yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False


@dataclass
class RenameIdentifiersScript:
    slug: str = "rename-identifiers"
    description: str = "Rename 'cast-id' front matter fields to 'id' and remove legacy version metadata."

    def run(self, ctx: ScriptContext) -> ScriptResult:
        root = ctx.root.expanduser().resolve()
        cast_dir = root / "Cast"
        config_path = root / ".cast" / "config.yaml"
        conflicts_dir = root / ".cast" / "conflicts"

        result = ScriptResult()

        # Update config.yaml if needed
        if config_path.exists():
            cfg_dirty = False
            data = yaml.load(config_path.read_text(encoding="utf-8")) or {}
            if "cast-id" in data:
                data["id"] = data.pop("cast-id")
                cfg_dirty = True
            if data.pop("cast-version", None) is not None:
                cfg_dirty = True
            if data.pop("base-version", None) is not None:
                cfg_dirty = True
            if cfg_dirty:
                result.updated_config = True
                result.notes.append(f"Updated config: {config_path}")
                if not ctx.dry_run:
                    with config_path.open("w", encoding="utf-8") as fh:
                        yaml.dump(data, fh)

        if cast_dir.exists():
            for md in cast_dir.rglob("*.md"):
                try:
                    fm, body, has_cast = parse_cast_file(md)
                except Exception:
                    continue
                if not has_cast or not isinstance(fm, dict):
                    continue

                changed = False
                if "cast-id" in fm:
                    fm["id"] = fm.pop("cast-id")
                    changed = True
                if fm.pop("cast-version", None) is not None:
                    changed = True
                if fm.pop("base-version", None) is not None:
                    changed = True

                if changed:
                    result.updated_files += 1
                    result.notes.append(f"Updated file: {md.relative_to(root)}")
                    if not ctx.dry_run:
                        write_cast_file(md, fm, body, reorder=True)

        if conflicts_dir.exists():
            result.removed_conflicts = True
            result.notes.append(f"Removed legacy conflict files in {conflicts_dir}")
            if not ctx.dry_run:
                shutil.rmtree(conflicts_dir, ignore_errors=True)

        return result


_script_instance = RenameIdentifiersScript()
register(RegisteredScript(_script_instance.slug, _script_instance.description, _script_instance.run))
