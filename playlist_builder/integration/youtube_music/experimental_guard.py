from __future__ import annotations


def is_ytmusicapi_installed() -> bool:
    """Return True when the optional ytmusicapi dependency is importable."""
    try:
        import ytmusicapi  # noqa: F401

        return True
    except ImportError:
        return False


def experimental_unavailable_reason() -> str:
    if is_ytmusicapi_installed():
        return ""
    return (
        "Module expérimental non installé. Installez l'extra Python "
        "`pip install playlist-builder[youtube]` ou importez un fichier JSON/CSV."
    )
