from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playlist_builder.ui.shared.theme.models import Theme, ThemeDefinition, ThemeError
from playlist_builder.ui.shared.theme.tokens import DesignTokens

MAX_THEME_FILE_BYTES = 256 * 1024


class ThemeLoadError(ThemeError):
    """Raised when a theme file cannot be parsed or resolved."""


def bundled_themes_dir() -> Path:
    return Path(__file__).resolve().parent / "themes"


def load_theme_file(path: Path) -> ThemeDefinition:
    if not path.is_file():
        raise ThemeLoadError(f"Fichier de thème introuvable : {path}")
    raw_bytes = path.read_bytes()
    if len(raw_bytes) > MAX_THEME_FILE_BYTES:
        raise ThemeLoadError(f"Fichier de thème trop volumineux : {path.name}")
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ThemeLoadError(f"JSON invalide dans {path.name} : {exc}") from exc
    if not isinstance(payload, dict):
        raise ThemeLoadError(f"Le thème {path.name} doit être un objet JSON.")
    return parse_theme_definition(payload, source=path.name)


def load_bundled_definitions() -> tuple[ThemeDefinition, ...]:
    themes_path = bundled_themes_dir()
    if not themes_path.is_dir():
        raise ThemeLoadError(f"Dossier de thèmes introuvable : {themes_path}")
    definitions: list[ThemeDefinition] = []
    for path in sorted(themes_path.glob("*.theme.json")):
        definitions.append(load_theme_file(path))
    if not definitions:
        raise ThemeLoadError("Aucun thème embarqué trouvé.")
    return tuple(definitions)


def resolve_definitions(definitions: tuple[ThemeDefinition, ...]) -> tuple[Theme, ...]:
    by_id = {definition.id: definition for definition in definitions}
    if len(by_id) != len(definitions):
        raise ThemeLoadError("Des identifiants de thème en double ont été détectés.")
    resolved: dict[str, Theme] = {}
    resolving: set[str] = set()

    def resolve_one(theme_id: str) -> Theme:
        if theme_id in resolved:
            return resolved[theme_id]
        definition = by_id.get(theme_id)
        if definition is None:
            raise ThemeLoadError(f"Thème parent introuvable : {theme_id!r}.")
        if theme_id in resolving:
            raise ThemeLoadError(f"Héritage de thème circulaire détecté pour {theme_id!r}.")
        resolving.add(theme_id)
        tokens = definition.tokens
        if definition.extends is not None:
            parent = resolve_one(definition.extends)
            tokens = parent.tokens.merge(definition.tokens)
        theme = Theme(
            id=definition.id,
            display_name=definition.display_name,
            version=definition.version,
            tokens=tokens,
            metadata=dict(definition.metadata),
            extends=definition.extends,
        )
        resolving.remove(theme_id)
        resolved[theme_id] = theme
        return theme

    return tuple(resolve_one(definition.id) for definition in definitions)


def parse_theme_definition(payload: dict[str, Any], *, source: str = "<inline>") -> ThemeDefinition:
    theme_id = _require_non_empty_string(payload.get("id"), field="id", source=source)
    display_name = _require_non_empty_string(payload.get("displayName"), field="displayName", source=source)
    version = _require_non_empty_string(payload.get("version"), field="version", source=source)
    extends = _optional_parent_id(payload.get("extends"), source=source)
    metadata = _parse_metadata(payload.get("metadata"), source=source)
    tokens = _parse_tokens(payload.get("tokens"), source=source)
    return ThemeDefinition(
        id=theme_id,
        display_name=display_name,
        version=version,
        tokens=tokens,
        metadata=metadata,
        extends=extends,
    )


def _parse_tokens(value: Any, *, source: str) -> DesignTokens:
    if value is None:
        return DesignTokens.empty()
    if not isinstance(value, dict):
        raise ThemeLoadError(f"Le champ tokens de {source} doit être un objet.")
    return DesignTokens(
        colors=_parse_string_map(value.get("colors"), field="colors", source=source),
        typography=_parse_string_map(value.get("typography"), field="typography", source=source),
        spacing=_parse_int_map(value.get("spacing"), field="spacing", source=source),
        radius=_parse_int_map(value.get("radius"), field="radius", source=source),
        shadows=_parse_string_map(value.get("shadows"), field="shadows", source=source),
    )


def _parse_metadata(value: Any, *, source: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ThemeLoadError(f"Le champ metadata de {source} doit être un objet.")
    metadata: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ThemeLoadError(f"metadata de {source} contient une clé invalide.")
        if not isinstance(item, str):
            raise ThemeLoadError(f"metadata.{key} de {source} doit être une chaîne.")
        metadata[key] = item
    return metadata


def _parse_string_map(value: Any, *, field: str, source: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ThemeLoadError(f"Le champ {field} de {source} doit être un objet.")
    parsed: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ThemeLoadError(f"{field} de {source} contient une clé invalide.")
        if not isinstance(item, str):
            raise ThemeLoadError(f"{field}.{key} de {source} doit être une chaîne.")
        parsed[key] = item
    return parsed


def _parse_int_map(value: Any, *, field: str, source: str) -> dict[str, int]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ThemeLoadError(f"Le champ {field} de {source} doit être un objet.")
    parsed: dict[str, int] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ThemeLoadError(f"{field} de {source} contient une clé invalide.")
        if not isinstance(item, int) or isinstance(item, bool):
            raise ThemeLoadError(f"{field}.{key} de {source} doit être un entier.")
        parsed[key] = item
    return parsed


def _require_non_empty_string(value: Any, *, field: str, source: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ThemeLoadError(f"Le champ {field} de {source} est requis.")
    return value.strip()


def _optional_parent_id(value: Any, *, source: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ThemeLoadError(f"Le champ extends de {source} doit être une chaîne non vide ou null.")
    return value.strip()
