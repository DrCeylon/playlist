from __future__ import annotations


class UnsupportedSchemaVersionError(Exception):
    """Raised when persisted data was written by a newer app version."""

    def __init__(self, found: int, supported: int, path: str) -> None:
        self.found = found
        self.supported = supported
        self.path = path
        super().__init__(
            f"Unsupported schema version {found} in {path} "
            f"(this application supports up to {supported})"
        )


class SnapshotChecksumMismatchError(Exception):
    """Raised when an on-disk snapshot file does not match its checksum key."""

    def __init__(self, path: str, expected: str, found: str) -> None:
        self.path = path
        self.expected = expected
        self.found = found
        super().__init__(
            f"Snapshot checksum mismatch in {path}: expected {expected!r}, found {found!r}"
        )


class SnapshotCorruptionError(Exception):
    """Raised when an existing snapshot file cannot be read or parsed."""

    def __init__(self, path: str, detail: str) -> None:
        self.path = path
        self.detail = detail
        super().__init__(f"Corrupt snapshot file {path}: {detail}")
