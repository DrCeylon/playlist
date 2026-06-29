from __future__ import annotations

import sys


def require_macos(feature: str = "Apple Music") -> None:
    if sys.platform != "darwin":
        raise SystemExit(
            f"Cet outil nécessite macOS pour accéder à {feature}. "
            f"Plateforme détectée: {sys.platform}."
        )
