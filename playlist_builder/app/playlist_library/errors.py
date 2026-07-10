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
