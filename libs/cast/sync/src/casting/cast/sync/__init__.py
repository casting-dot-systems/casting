"""Cast Sync - 3-way sync engine and conflict handling."""

from casting.cast.sync.conflict import ConflictResolution, handle_conflict
from casting.cast.sync.hsync import HorizontalSync, SyncDecision, SyncPlan
from casting.cast.sync.index import build_ephemeral_index
from casting.cast.sync.cbsync import CodebaseSync

__all__ = [
    "HorizontalSync",
    "SyncDecision",
    "SyncPlan",
    "ConflictResolution",
    "handle_conflict",
    "build_ephemeral_index",
    "CodebaseSync",
]

__version__ = "0.2.2"
