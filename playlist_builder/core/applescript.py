from __future__ import annotations

import subprocess


def apple_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def format_applescript_error(stderr: str) -> str:
    """Return an actionable French message for common Music.app automation failures."""
    lowered = stderr.lower()
    if (
        "not authorized" in lowered
        or "automation" in lowered
        or "-1743" in stderr
        or "autorisation" in lowered
        or "assistive access" in lowered
    ):
            return (
            "Autorise Resonance ou Terminal à contrôler Music dans "
            "Réglages Système > Confidentialité et sécurité > Automatisation."
        )
    if "music got an error" in lowered and "not running" in lowered:
        return "Music.app n'est pas lancé. Ouvre Music.app puis relance l'import."
    return stderr.strip() or "Échec AppleScript vers Music.app."


def run_applescript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(format_applescript_error(result.stderr.strip() or result.stdout.strip()))
    return result.stdout.strip()
