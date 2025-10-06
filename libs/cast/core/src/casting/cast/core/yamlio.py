"""YAML front matter parsing and manipulation."""

import re
import re as _re
import uuid
from io import StringIO
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

# Initialize YAML parser with round-trip preservation
yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False
yaml.width = 4096  # Avoid line wrapping

# Known cast keys we prefer to show first in the "cast-* properties" section.
_KNOWN_CAST_KEYS_IN_MIDDLE = ["cast-hsync", "cast-codebases"]
VAULT_ENTRY_REGEX = re.compile(r"^\s*(?P<name>[^()]+?)\s*\((?P<mode>live|watch)\)\s*$")
FM_RE = _re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?", _re.DOTALL)


def _canonicalize_cast_lists(front_matter: dict[str, Any]) -> dict[str, Any]:
    """
    Canonicalize list-style cast fields for deterministic output:
      • cast-hsync: keep valid 'Name (live|watch)' entries, dedup by name
        (prefer 'live' if both present), then sort alphabetically by name.
      • cast-codebases: ensure list[str], dedup, and alpha-sort (casefold).
    """
    fm = dict(front_matter or {})

    # ---- cast-hsync ----
    hs = fm.get("cast-hsync")
    if hs is not None:
        if isinstance(hs, str):
            hs = [hs]
        if not isinstance(hs, list):
            hs = []
        modes_by_name: dict[str, str] = {}
        for entry in hs:
            if not isinstance(entry, str):
                continue
            m = VAULT_ENTRY_REGEX.match(entry)
            if not m:
                continue
            name = (m.group("name") or "").strip()
            mode = m.group("mode")
            if not name:
                continue
            prev = modes_by_name.get(name)
            # Prefer 'live' when duplicates conflict
            if prev == "live":
                continue
            if prev == "watch" and mode == "live":
                modes_by_name[name] = "live"
            elif prev is None:
                modes_by_name[name] = mode
        if modes_by_name:
            names = sorted(modes_by_name.keys(), key=str.casefold)
            fm["cast-hsync"] = [f"{n} ({modes_by_name[n]})" for n in names]
        else:
            fm["cast-hsync"] = []

    # ---- cast-codebases ----
    cbs = fm.get("cast-codebases")
    if cbs is not None:
        if isinstance(cbs, str):
            cbs = [cbs]
        if isinstance(cbs, list):
            vals = [str(x).strip() for x in cbs if str(x).strip()]
            uniq = sorted(set(vals), key=str.casefold)
            fm["cast-codebases"] = uniq
        else:
            fm["cast-codebases"] = []

    return fm


def parse_cast_file(filepath: Path) -> tuple[dict[str, Any] | None, str, bool]:
    """
    Parse a Markdown file with YAML front matter.

    Returns:
        (front_matter, body, has_cast_fields)
    """
    content = filepath.read_text(encoding="utf-8")

    # Find front matter (supports LF and CRLF)
    m = FM_RE.match(content)
    if not m:
        return None, content, False

    yaml_text = m.group(1)
    body = content[m.end() :]

    try:
        front_matter = yaml.load(yaml_text)
        if not isinstance(front_matter, dict):
            return None, content, False
    except YAMLError:
        return None, content, False

    # Check if it has any cast-* fields
    has_cast_fields = any(isinstance(k, str) and (k.startswith("cast-") or k == "id") for k in front_matter)

    return front_matter, body, has_cast_fields


def extract_cast_fields(front_matter: dict[str, Any]) -> dict[str, Any]:
    """Extract Cast-related fields (including ``id``) from front matter."""
    return {k: v for k, v in front_matter.items() if isinstance(k, str) and (k.startswith("cast-") or k == "id")}


def parse_hsync_entries(entries: list[str] | None) -> dict[str, str]:
    """
    Parse cast-hsync entries into {name: mode} dict.
    Invalid entries are ignored. Values remain 'live' or 'watch'.
    """
    if not entries:
        return {}

    result = {}
    for entry in entries:
        if not isinstance(entry, str):
            continue
        match = VAULT_ENTRY_REGEX.match(entry)
        if match:
            result[match.group("name")] = match.group("mode")

    return result


#
# Legacy alias for any internal callers not yet updated (harmless if removed later).
parse_vault_entries = parse_hsync_entries


def ensure_cast_fields(front_matter: dict[str, Any], generate_id: bool = True) -> tuple[dict[str, Any], bool]:
    """
    Ensure ``id`` exists and validate cast-vaults format.

    Returns:
        (updated_front_matter, was_modified)
    """
    modified = False

    if "last-updated" not in front_matter:
        front_matter["last-updated"] = ""

    if generate_id:
        id_present = "id" in front_matter
        current_id = front_matter.get("id") if id_present else None
        id_missing = not id_present or current_id is None
        id_blank = isinstance(current_id, str) and current_id.strip() == ""

        if id_missing or id_blank:
            front_matter["id"] = str(uuid.uuid4())
            modified = True

    # Remove legacy version markers if still present
    if front_matter.pop("cast-version", None) is not None:
        modified = True
    if front_matter.pop("base-version", None) is not None:
        modified = True

    # NOTE: Do not mutate 'cast-hsync' here. Invalid entries are handled at routing time.

    return front_matter, modified


def reorder_cast_fields(front_matter: dict[str, Any]) -> dict[str, Any]:
    """
    Canonicalize lists and reorder YAML to the canonical layout:
      1) last-updated
      2) id
      3) cast-* properties (known first, then any others alphabetically)
      4) all remaining (non-cast) fields in their original order
    """
    fm = _canonicalize_cast_lists(dict(front_matter or {}))
    result: dict[str, Any] = {}

    # Partition
    cast_fields: dict[str, Any] = {}
    other_fields: dict[str, Any] = {}
    for k, v in fm.items():
        if isinstance(k, str) and k.startswith("cast-"):
            cast_fields[k] = v
        else:
            other_fields[k] = v

    # 1) last-updated
    if "last-updated" in other_fields:
        result["last-updated"] = other_fields.pop("last-updated")

    # 2) id (preferred)
    if "id" in other_fields:
        result["id"] = other_fields.pop("id")
    elif "id" in cast_fields:
        result["id"] = cast_fields.pop("id")

    # 3) cast-* properties (excluding version)
    #    3a) known keys in a stable order
    for k in _KNOWN_CAST_KEYS_IN_MIDDLE:
        if k in cast_fields:
            result[k] = cast_fields.pop(k)
    #    3b) any remaining cast-* (excluding version), alphabetical
    middle_keys = sorted(cast_fields.keys(), key=str.casefold)
    for k in middle_keys:
        result[k] = cast_fields.pop(k)

    # 4) Remaining (non-cast) fields in original order
    for k, v in other_fields.items():
        result[k] = v

    return result


def write_cast_file(filepath: Path, front_matter: dict[str, Any], body: str, reorder: bool = True) -> None:
    """Write a Markdown file with YAML front matter."""
    # Migrate legacy field name inline if still present
    if "cast-vaults" in front_matter and "cast-hsync" not in front_matter:
        front_matter["cast-hsync"] = front_matter.pop("cast-vaults")
    # Drop deprecated fields
    front_matter.pop("cast-version", None)
    front_matter.pop("base-version", None)
    # Always canonicalize lists; optionally reorder keys
    front_matter = reorder_cast_fields(front_matter) if reorder else _canonicalize_cast_lists(front_matter)

    # Write YAML to string
    stream = StringIO()
    yaml.dump(front_matter, stream)
    yaml_text = stream.getvalue()

    # Combine with body
    content = f"---\n{yaml_text}---\n{body}"

    # Write atomically
    temp_path = filepath.parent / f".{filepath.name}.casttmp"
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(filepath)


def ensure_codebase_membership(
    front_matter: dict[str, Any], *, codebase: str, origin_cast: str
) -> tuple[dict[str, Any], bool]:
    """
    Ensure a note is ready to participate in a codebase:
      - id present (delegates to ensure_cast_fields)
      - 'cast-codebases' includes `codebase`
      - 'cast-hsync' includes '<origin_cast> (live)'
    """
    fm_in = dict(front_matter or {})
    fm = dict(fm_in)
    fm, modified = ensure_cast_fields(fm, generate_id=True)

    # cast-codebases: normalize to list and include codebase
    cbs = fm.get("cast-codebases")
    if cbs is None:
        cbs = []
    if isinstance(cbs, str):
        cbs = [cbs]
    if codebase not in cbs:
        cbs.append(codebase)
        modified = True
    fm["cast-codebases"] = cbs

    # cast-hsync: ensure origin exists as '<origin_cast> (live)'
    origin_entry = f"{origin_cast} (live)"
    hs = fm.get("cast-hsync")
    if hs is None:
        hs = []
    if isinstance(hs, str):
        hs = [hs]
    if origin_entry not in hs:
        hs.append(origin_entry)
        modified = True
    fm["cast-hsync"] = hs
    # Canonicalize lists; record if that changed anything
    fm_canon = _canonicalize_cast_lists(fm)
    if fm_canon.get("cast-hsync") != (fm_in.get("cast-hsync")):
        modified = True
    if fm_canon.get("cast-codebases") != (fm_in.get("cast-codebases")):
        modified = True
    return fm_canon, modified
