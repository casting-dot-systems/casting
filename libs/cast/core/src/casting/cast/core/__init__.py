"""Cast Core - parsing, normalization, and digest utilities."""

from casting.cast.core.digest import compute_digest, normalize_yaml_for_digest
from casting.cast.core.models import (
    CastConfig,
    FileRec,
    SyncState,
    SyncStateEntry,
)
from casting.cast.core.registry import (
    cast_home_dir,
    list_casts,
    load_registry,
    register_cast,
    registry_path,
    resolve_cast_by_id,
    resolve_cast_by_name,
    save_registry,
    unregister_cast,
    # codebases
    list_codebases,
    register_codebase,
    resolve_codebase_by_name,
    unregister_codebase,
)
from casting.cast.core.yamlio import (
    ensure_cast_fields,
    ensure_codebase_membership,
    extract_cast_fields,
    parse_cast_file,
    reorder_cast_fields,
    write_cast_file,
)

__all__ = [
    "compute_digest",
    "normalize_yaml_for_digest",
    # registry
    "cast_home_dir",
    "registry_path",
    "load_registry",
    "save_registry",
    "register_cast",
    "list_casts",
    "resolve_cast_by_name",
    "resolve_cast_by_id",
    "unregister_cast",
    # codebases
    "list_codebases",
    "register_codebase",
    "resolve_codebase_by_name",
    "unregister_codebase",
    "CastConfig",
    "FileRec",
    "SyncState",
    "SyncStateEntry",
    "parse_cast_file",
    "extract_cast_fields",
    "ensure_cast_fields",
    "ensure_codebase_membership",
    "reorder_cast_fields",
    "write_cast_file",
]

__version__ = "0.2.1"
