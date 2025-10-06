from __future__ import annotations

import sys
from pathlib import Path


def _find_workspace_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def _iter_src_dirs(root: Path) -> list[Path]:
    results: list[Path] = []
    seen: set[Path] = set()
    for base in (root / "apps", root / "libs", root / "llmgine"):
        if not base.exists():
            continue
        for candidate in base.rglob("src"):
            if candidate.is_dir():
                resolved = candidate.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    results.append(resolved)
    return results


_ROOT = _find_workspace_root(Path(__file__).resolve())
for _path in _iter_src_dirs(_ROOT):
    sys.path.insert(0, str(_path))
