from __future__ import annotations

from enum import StrEnum


class ConflictKind(StrEnum):
    """Provider-neutral conflict taxonomy for playlist sync."""

    DUPLICATE_LOCAL = "duplicate_local"
    DUPLICATE_REMOTE = "duplicate_remote"
    METADATA_MISMATCH = "metadata_mismatch"
    ORDER_MISMATCH = "order_mismatch"
    RENAME_MISMATCH = "rename_mismatch"
    DELETION_LOCAL = "deletion_local"
    DELETION_REMOTE = "deletion_remote"
    MISSING_LOCAL = "missing_local"
    MISSING_REMOTE = "missing_remote"
    CONCURRENT_MODIFICATION = "concurrent_modification"
    PROVIDER_LINK_MISMATCH = "provider_link_mismatch"
    VERSION_LOCAL_STALE = "version_local_stale"
    VERSION_REMOTE_STALE = "version_remote_stale"
    UNSUPPORTED_ACTION = "unsupported_action"
    # Legacy aliases
    DUPLICATE = "duplicate"
    METADATA = "metadata_mismatch"


class ConflictScope(StrEnum):
    PLAYLIST = "playlist"
    TRACK = "track"
    LINK = "link"
    VERSION = "version"


class ConflictSeverity(StrEnum):
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


class ConflictResolutionStrategy(StrEnum):
    KEEP_LOCAL = "keep_local"
    KEEP_REMOTE = "keep_remote"
    MERGE = "merge"
    IGNORE = "ignore"
    DEFER = "defer"


DEFAULT_RESOLUTIONS_BY_KIND: dict[str, tuple[str, ...]] = {
    ConflictKind.DUPLICATE_LOCAL.value: (
        ConflictResolutionStrategy.KEEP_LOCAL.value,
        ConflictResolutionStrategy.KEEP_REMOTE.value,
        ConflictResolutionStrategy.IGNORE.value,
        ConflictResolutionStrategy.DEFER.value,
    ),
    ConflictKind.DUPLICATE_REMOTE.value: (
        ConflictResolutionStrategy.KEEP_LOCAL.value,
        ConflictResolutionStrategy.KEEP_REMOTE.value,
        ConflictResolutionStrategy.IGNORE.value,
        ConflictResolutionStrategy.DEFER.value,
    ),
    ConflictKind.METADATA_MISMATCH.value: (
        ConflictResolutionStrategy.KEEP_LOCAL.value,
        ConflictResolutionStrategy.KEEP_REMOTE.value,
        ConflictResolutionStrategy.MERGE.value,
        ConflictResolutionStrategy.DEFER.value,
    ),
    ConflictKind.ORDER_MISMATCH.value: (
        ConflictResolutionStrategy.KEEP_LOCAL.value,
        ConflictResolutionStrategy.KEEP_REMOTE.value,
        ConflictResolutionStrategy.DEFER.value,
    ),
    ConflictKind.RENAME_MISMATCH.value: (
        ConflictResolutionStrategy.KEEP_LOCAL.value,
        ConflictResolutionStrategy.KEEP_REMOTE.value,
        ConflictResolutionStrategy.DEFER.value,
    ),
    ConflictKind.DELETION_LOCAL.value: (
        ConflictResolutionStrategy.KEEP_LOCAL.value,
        ConflictResolutionStrategy.KEEP_REMOTE.value,
        ConflictResolutionStrategy.DEFER.value,
    ),
    ConflictKind.DELETION_REMOTE.value: (
        ConflictResolutionStrategy.KEEP_LOCAL.value,
        ConflictResolutionStrategy.KEEP_REMOTE.value,
        ConflictResolutionStrategy.DEFER.value,
    ),
    ConflictKind.MISSING_LOCAL.value: (
        ConflictResolutionStrategy.KEEP_REMOTE.value,
        ConflictResolutionStrategy.IGNORE.value,
        ConflictResolutionStrategy.DEFER.value,
    ),
    ConflictKind.MISSING_REMOTE.value: (
        ConflictResolutionStrategy.KEEP_LOCAL.value,
        ConflictResolutionStrategy.IGNORE.value,
        ConflictResolutionStrategy.DEFER.value,
    ),
    ConflictKind.CONCURRENT_MODIFICATION.value: (
        ConflictResolutionStrategy.DEFER.value,
        ConflictResolutionStrategy.KEEP_LOCAL.value,
        ConflictResolutionStrategy.KEEP_REMOTE.value,
    ),
    ConflictKind.PROVIDER_LINK_MISMATCH.value: (
        ConflictResolutionStrategy.DEFER.value,
        ConflictResolutionStrategy.IGNORE.value,
    ),
}


def recommended_resolution_for_kind(kind: str) -> str:
    options = DEFAULT_RESOLUTIONS_BY_KIND.get(kind, ())
    if ConflictResolutionStrategy.DEFER.value in options:
        return ConflictResolutionStrategy.DEFER.value
    return options[0] if options else ConflictResolutionStrategy.DEFER.value
