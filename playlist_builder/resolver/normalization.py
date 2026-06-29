from __future__ import annotations

import re
import unicodedata

_NOISE_PATTERNS = (
    r"\bfeat\.?\b.*$",
    r"\bfeaturing\b.*$",
    r"\bfrom\b.*$",
)

_BRACKETED_PATTERN = re.compile(r"\s*[\[(].*?[\])]")
_NON_WORD_PATTERN = re.compile(r"[^a-z0-9]+")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    """Normalize text for robust matching.

    Keeps the function intentionally dependency-free and deterministic. It is
    used both by Python scoring and by generated AppleScript query variants.
    """

    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower().replace("&", " and ")
    text = _BRACKETED_PATTERN.sub(" ", text)
    for pattern in _NOISE_PATTERNS:
        text = re.sub(pattern, " ", text)
    text = _NON_WORD_PATTERN.sub(" ", text)
    return _WHITESPACE_PATTERN.sub(" ", text).strip()


def token_set(value: str) -> set[str]:
    return {token for token in normalize_text(value).split() if token}
