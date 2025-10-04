"""Ephemeral index building for casts."""

import logging
from pathlib import Path

from casting.cast.core import (
    compute_digest,
    ensure_cast_fields,
    extract_cast_fields,
    parse_cast_file,
    write_cast_file,
)
from casting.cast.core.models import FileRec
from casting.cast.core.yamlio import parse_hsync_entries, reorder_cast_fields

logger = logging.getLogger(__name__)


class EphemeralIndex:
    """In-memory index of a cast's files."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.by_id: dict[str, FileRec] = {}
        self.by_path: dict[str, str] = {}  # relpath -> id

    def add_file(self, rec: FileRec) -> None:
        """Add a file record to the index."""
        self.by_id[rec["id"]] = rec
        self.by_path[rec["relpath"]] = rec["id"]

    def get_by_id(self, identifier: str) -> FileRec | None:
        """Get file record by id."""
        return self.by_id.get(identifier)

    def get_by_path(self, relpath: str) -> FileRec | None:
        """Get file record by relative path."""
        identifier = self.by_path.get(relpath)
        return self.by_id.get(identifier) if identifier else None

    def all_peers(self) -> set[str]:
        """Get all unique peer names referenced."""
        peers = set()
        for rec in self.by_id.values():
            peers.update(rec["peers"].keys())
        return peers

    def all_codebases(self) -> set[str]:
        """Get all unique codebase names referenced."""
        codebases = set()
        for rec in self.by_id.values():
            codebases.update(rec["codebases"])
        return codebases


def build_ephemeral_index(
    root_path: Path, vault_path: Path, fixup: bool = True, limit_file: str | None = None
) -> EphemeralIndex:
    """
    Build an ephemeral index of cast files in a cast folder.

    Args:
        root_path: Path to Cast root (contains .cast/)
        vault_path: Path to cast folder
        fixup: Whether to fix missing id and reorder fields
        limit_file: Optional id or relpath to limit indexing to one file

    Returns:
        EphemeralIndex instance
    """
    index = EphemeralIndex(vault_path)

    # Find all Markdown files
    md_files: list[Path] = []
    if limit_file:
        # Normalize limit_file to a path relative to the cast folder, supporting:
        #  - absolute paths under the cast folder
        #  - callers that include the cast folder prefix (e.g. "Cast/foo.md")
        lf = Path(limit_file)
        candidates: list[Path] = []

        if lf.is_absolute():
            try:
                candidates.append(lf.relative_to(vault_path))
            except ValueError:
                # Not under this cast folder; leave empty so we fall back to id lookup.
                pass
        else:
            if lf.parts and lf.parts[0] == vault_path.name:
                candidates.append(Path(*lf.parts[1:]))
            candidates.append(lf)

        for rel in candidates:
            cand = vault_path / rel
            if cand.exists():
                md_files = [cand]
                break

        if not md_files:
            # Maybe limit_file was an id; scan all and resolve by id below.
            md_files = list(vault_path.rglob("*.md"))
    else:
        md_files = list(vault_path.rglob("*.md"))

    for md_path in md_files:
        try:
            # Parse file
            front_matter, body, has_cast_fields = parse_cast_file(md_path)

            if not has_cast_fields:
                continue

            # Ensure cast fields and canonicalize order (including last-updated first)
            if fixup and front_matter:
                modified = False
                # Legacy migration: cast-vaults -> cast-hsync
                if "cast-vaults" in front_matter and "cast-hsync" not in front_matter:
                    front_matter["cast-hsync"] = front_matter.pop("cast-vaults")
                    modified = True
                front_matter, fields_modified = ensure_cast_fields(front_matter, generate_id=True)
                modified = modified or fields_modified

                # Determine if YAML needs reordering even if no fields were added
                need_reorder = False
                try:
                    keys = list(front_matter.keys())
                    # Enforce 'last-updated' first when present
                    if "last-updated" in front_matter:
                        if not keys or keys[0] != "last-updated":
                            need_reorder = True
                    # Enforce canonical cast-* ordering
                    # Compare current mapping to reorder_cast_fields result
                    # (this catches list canonicalization for 'cast-hsync' and 'cast-codebases')
                    reordered = reorder_cast_fields(dict(front_matter))
                    if list(reordered.keys()) != keys:
                        need_reorder = True
                    else:
                        if reordered.get("cast-hsync") != front_matter.get("cast-hsync"):
                            need_reorder = True
                        if reordered.get("cast-codebases") != front_matter.get("cast-codebases"):
                            need_reorder = True
                except Exception:
                    # If we can't inspect order, be conservative and rewrite
                    need_reorder = True

                if modified or need_reorder:
                    write_cast_file(md_path, front_matter, body, reorder=True)
                    logger.info(f"Fixed cast fields/order in {md_path}")

            identifier = None
            if front_matter:
                identifier = front_matter.get("id")

            if not front_matter or not identifier:
                continue

            # Extract cast fields
            cast_fields = extract_cast_fields(front_matter)
            file_id = cast_fields.get("id") or identifier

            # Parse hsync entries
            hsync_entries = cast_fields.get("cast-hsync") or cast_fields.get("cast-vaults", [])
            peers = parse_hsync_entries(hsync_entries)

            # Get codebases
            codebases = cast_fields.get("cast-codebases", [])
            if not isinstance(codebases, list):
                codebases = []

            # Compute digest
            digest = compute_digest(front_matter, body)

            # Create record
            relpath = str(md_path.relative_to(vault_path))
            rec: FileRec = {
                "id": file_id,
                "relpath": relpath,
                "digest": digest,
                "peers": peers,
                "codebases": codebases,
            }

            index.add_file(rec)

            # If we were looking for a specific file by id
            if limit_file and file_id == limit_file:
                break

        except Exception as e:
            logger.warning(f"Error indexing {md_path}: {e}")
            continue

    return index
