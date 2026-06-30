from __future__ import annotations

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.enums import EnergyCurveProfile, ExclusionKind
from playlist_builder.ui.shared.dto.generation import (
    EnergyCurveOption,
    ExclusionRule,
    PlaylistGenerationRequest,
    SeedReference,
)
from playlist_builder.ui.shared.dto.preferences import UserPreferences
from playlist_builder.ui.shared.validation import ValidationError, ValidationResult, merge_results

_VALID_EXCLUSION_KINDS = frozenset(ExclusionKind)
_VALID_ENERGY_PROFILES = frozenset(EnergyCurveProfile)


def validate_playlist_name(name: str) -> ValidationResult:
    if not name.strip():
        return ValidationResult((ValidationError("name", "Le nom de la playlist est obligatoire."),))
    if len(name.strip()) > 120:
        return ValidationResult((ValidationError("name", "Le nom ne doit pas dépasser 120 caractères."),))
    return ValidationResult()


def validate_provider_id(provider_id: ProviderId) -> ValidationResult:
    if provider_id is None:
        return ValidationResult((ValidationError("provider_id", "Un fournisseur est requis."),))
    return ValidationResult()


def validate_seeds_or_keywords(
    seeds: tuple[SeedReference, ...],
    keywords: tuple[str, ...],
) -> ValidationResult:
    has_seed = any(seed.artist.strip() or seed.title.strip() for seed in seeds)
    has_keywords = any(keyword.strip() for keyword in keywords)
    if has_seed or has_keywords:
        return ValidationResult()
    return ValidationResult(
        (
            ValidationError(
                "seeds",
                "Au moins une graine (artiste/morceau) ou un mot-clé est requis.",
            ),
        )
    )


def validate_target_size(
    target_track_count: int | None,
    target_duration_minutes: int | None,
) -> ValidationResult:
    if target_track_count is None and target_duration_minutes is None:
        return ValidationResult(
            (
                ValidationError(
                    "target_track_count",
                    "Le nombre de morceaux ou la durée cible est requis.",
                ),
            )
        )
    errors: list[ValidationError] = []
    if target_track_count is not None and target_track_count <= 0:
        errors.append(ValidationError("target_track_count", "Le nombre de morceaux doit être positif."))
    if target_duration_minutes is not None and target_duration_minutes <= 0:
        errors.append(ValidationError("target_duration_minutes", "La durée cible doit être positive."))
    return ValidationResult(errors=tuple(errors))


def validate_exclusion_rule(rule: ExclusionRule) -> ValidationResult:
    if rule.kind not in _VALID_EXCLUSION_KINDS:
        return ValidationResult(
            (ValidationError("exclusions.kind", f"Type d'exclusion invalide : {rule.kind!r}."),)
        )
    if not rule.value.strip():
        return ValidationResult(
            (ValidationError("exclusions.value", "La valeur d'exclusion ne peut pas être vide."),)
        )
    return ValidationResult()


def validate_energy_curve(curve: EnergyCurveOption) -> ValidationResult:
    if curve.profile not in _VALID_ENERGY_PROFILES:
        return ValidationResult(
            (ValidationError("energy_curve.profile", f"Profil d'énergie invalide : {curve.profile!r}."),)
        )
    return ValidationResult()


def validate_playlist_generation_request(request: PlaylistGenerationRequest) -> ValidationResult:
    results = [
        validate_playlist_name(request.name),
        validate_provider_id(request.provider_id),
        validate_seeds_or_keywords(request.seeds, request.keywords),
        validate_target_size(request.target_track_count, request.target_duration_minutes),
        validate_energy_curve(request.energy_curve),
    ]
    for rule in request.exclusions:
        results.append(validate_exclusion_rule(rule))
    return merge_results(*results)


def validate_user_preferences(preferences: UserPreferences) -> ValidationResult:
    errors: list[ValidationError] = []
    if not preferences.country_code.strip():
        errors.append(ValidationError("country_code", "Le code pays est requis."))
    if not preferences.theme_id.strip():
        errors.append(ValidationError("theme_id", "Un thème est requis."))
    if preferences.locale not in {"fr", "en"}:
        errors.append(ValidationError("locale", "La locale doit être 'fr' ou 'en'."))
    return ValidationResult(errors=tuple(errors))
