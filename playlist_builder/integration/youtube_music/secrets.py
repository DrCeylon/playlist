from __future__ import annotations

import re
from typing import Any

_FORBIDDEN_KEY_FRAGMENTS = (
    "cookie",
    "token",
    "authorization",
    "auth_header",
    "oauth",
    "secret",
    "password",
    "session",
    "bearer",
    "sapisi",
    "header",
)

_FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"SAPISID=\S+", re.IGNORECASE),
    re.compile(r"__Secure-\S+", re.IGNORECASE),
    re.compile(r"Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"(Cookie|Authorization|token)\s*[:=]\s*\S+", re.IGNORECASE),
)


def sanitize_user_message(message: str) -> str:
    """Remove likely credential fragments from provider error messages."""
    cleaned = message
    for pattern in _FORBIDDEN_VALUE_PATTERNS:
        cleaned = pattern.sub("[redacted]", cleaned)
    if len(cleaned) > 240:
        cleaned = cleaned[:237] + "..."
    return cleaned.strip()


def contains_secret_key(key: str) -> bool:
    lowered = key.strip().lower()
    return any(fragment in lowered for fragment in _FORBIDDEN_KEY_FRAGMENTS)


def assert_bridge_safe_mapping(payload: dict[str, Any], *, context: str = "") -> None:
    """Fail fast when a bridge payload appears to include credential material."""
    for key, value in payload.items():
        if contains_secret_key(str(key)):
            raise ValueError(f"Secret-like key in bridge payload{f' ({context})' if context else ''}: {key}")
        if isinstance(value, dict):
            assert_bridge_safe_mapping(value, context=context or str(key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    assert_bridge_safe_mapping(item, context=f"{context}[{index}]")
