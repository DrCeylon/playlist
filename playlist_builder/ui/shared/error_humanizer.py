"""User-facing error messages — never expose raw Python internals to clients."""

from __future__ import annotations

import re
from typing import Final

_TECHNICAL_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"cannot access local variable", re.IGNORECASE),
    re.compile(r"unboundlocalerror", re.IGNORECASE),
    re.compile(r"nameerror", re.IGNORECASE),
    re.compile(r"attributeerror", re.IGNORECASE),
    re.compile(r"typeerror", re.IGNORECASE),
    re.compile(r"traceback \(most recent call last\)", re.IGNORECASE),
    re.compile(r"^\s*file \"", re.IGNORECASE),
    re.compile(r"line \d+, in ", re.IGNORECASE),
)

_IMPORT_CONTEXTS: Final[frozenset[str]] = frozenset(
    {
        "import_playlist",
        "continue_manual_acquisition",
        "probe_manual_acquisition",
    }
)


def is_technical_error_message(message: str) -> bool:
    """Return True when *message* looks like a Python/runtime internal error."""
    trimmed = message.strip()
    if not trimmed:
        return False
    return any(pattern.search(trimmed) for pattern in _TECHNICAL_PATTERNS)


def humanize_engine_error(message: str, *, context: str = "") -> tuple[str, tuple[tuple[str, str], ...]]:
    """Return a user-safe message and optional technical details for diagnostics."""
    trimmed = message.strip()
    if not trimmed:
        return (
            _default_message(context),
            (),
        )
    if not is_technical_error_message(trimmed):
        return trimmed, ()

    return (
        _default_message(context),
        (("technical", trimmed),),
    )


def _default_message(context: str) -> str:
    if context in _IMPORT_CONTEXTS:
        return (
            "L'importation a échoué pendant la préparation. "
            "Vous pouvez réessayer ou consulter le détail technique."
        )
    return "Une erreur interne s'est produite. Réessayez ou consultez le diagnostic technique."
