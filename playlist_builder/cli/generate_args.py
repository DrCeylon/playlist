from __future__ import annotations

from playlist_builder.canonical.constants import DEFAULT_PLAYLIST_DESCRIPTION
from playlist_builder.core.models import TrackRef
from playlist_builder.planning.models import (
    ConstraintKind,
    EnergyProfile,
    ExclusionRule,
    GenerationConstraints,
    InclusionRule,
    PlaylistRequest,
    SeedTrack,
)

_CONSTRAINT_KIND_ALIASES = {
    "artist": ConstraintKind.ARTIST,
    "album": ConstraintKind.ALBUM,
    "track": ConstraintKind.TRACK,
    "genre": ConstraintKind.GENRE,
    "mood": ConstraintKind.MOOD,
    "language": ConstraintKind.LANGUAGE,
    "term": ConstraintKind.TERM,
}


def parse_seed_track(value: str) -> SeedTrack:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Un seed ne peut pas être vide.")

    if ":" in cleaned:
        artist, title = cleaned.split(":", 1)
    elif " - " in cleaned:
        artist, title = cleaned.split(" - ", 1)
    else:
        raise ValueError(
            "Format de seed invalide. Utilisez 'Artiste:Titre' ou 'Artiste - Titre'."
        )

    artist = artist.strip()
    title = title.strip()
    if not artist or not title:
        raise ValueError("Un seed doit contenir un artiste et un titre.")

    return SeedTrack(TrackRef(artist=artist, title=title))


def parse_csv_terms(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(term.strip() for term in value.split(",") if term.strip())


def parse_exclusion_rule(value: str) -> ExclusionRule:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Une exclusion ne peut pas être vide.")

    if ":" in cleaned:
        kind_name, rule_value = cleaned.split(":", 1)
        kind = _parse_constraint_kind(kind_name)
        rule_value = rule_value.strip()
        if not rule_value:
            raise ValueError(f"Exclusion '{value}' invalide: valeur manquante.")
        return ExclusionRule(kind=kind, value=rule_value)

    return ExclusionRule(kind=ConstraintKind.TERM, value=cleaned)


def parse_inclusion_rule(value: str) -> InclusionRule:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Une inclusion ne peut pas être vide.")

    weight = 1.0
    if ":" in cleaned:
        parts = cleaned.split(":")
        if len(parts) == 3:
            kind_name, rule_value, weight_text = parts
            weight = _parse_weight(weight_text)
        elif len(parts) == 2:
            kind_name, rule_value = parts
        else:
            raise ValueError(f"Inclusion '{value}' invalide.")
        kind = _parse_constraint_kind(kind_name)
        rule_value = rule_value.strip()
        if not rule_value:
            raise ValueError(f"Inclusion '{value}' invalide: valeur manquante.")
        return InclusionRule(kind=kind, value=rule_value, weight=weight)

    return InclusionRule(kind=ConstraintKind.TERM, value=cleaned, weight=weight)


def parse_energy_profile(value: str) -> EnergyProfile:
    try:
        return EnergyProfile(value.strip().lower())
    except ValueError as exc:
        allowed = ", ".join(profile.value for profile in EnergyProfile)
        raise ValueError(f"Profil d'énergie invalide '{value}'. Valeurs possibles: {allowed}.") from exc


def build_playlist_request(
    *,
    name: str,
    seeds: list[str],
    keywords: tuple[str, ...] = (),
    excludes: tuple[str, ...] = (),
    includes: tuple[str, ...] = (),
    track_count: int | None = None,
    duration_minutes: int | None = None,
    energy_profile: EnergyProfile = EnergyProfile.RISING,
    allow_explicit: bool = True,
    description: str = DEFAULT_PLAYLIST_DESCRIPTION,
) -> PlaylistRequest:
    if track_count is None and duration_minutes is None:
        raise ValueError("Indiquez --tracks ou --duration.")

    parsed_seeds = tuple(parse_seed_track(seed) for seed in seeds)
    if not parsed_seeds:
        raise ValueError("Au moins un --seed est requis.")

    exclusions = tuple(parse_exclusion_rule(value) for value in excludes)
    inclusions = tuple(parse_inclusion_rule(value) for value in includes)

    return PlaylistRequest(
        name=name.strip(),
        seeds=parsed_seeds,
        constraints=GenerationConstraints(
            target_track_count=track_count,
            target_duration_minutes=duration_minutes,
            energy_profile=energy_profile,
            preferred_terms=keywords,
            excluded_terms=tuple(
                rule.value for rule in exclusions if rule.kind == ConstraintKind.TERM
            ),
            exclusions=tuple(rule for rule in exclusions if rule.kind != ConstraintKind.TERM),
            inclusions=inclusions,
            allow_explicit=allow_explicit,
        ),
        description=description.strip() or DEFAULT_PLAYLIST_DESCRIPTION,
    )


def _parse_constraint_kind(value: str) -> ConstraintKind:
    kind = _CONSTRAINT_KIND_ALIASES.get(value.strip().lower())
    if kind is None:
        allowed = ", ".join(sorted(_CONSTRAINT_KIND_ALIASES))
        raise ValueError(f"Type de contrainte invalide '{value}'. Valeurs possibles: {allowed}.")
    return kind


def _parse_weight(value: str) -> float:
    try:
        weight = float(value.strip())
    except ValueError as exc:
        raise ValueError(f"Poids d'inclusion invalide '{value}'.") from exc
    if weight <= 0:
        raise ValueError("Le poids d'une inclusion doit être positif.")
    return weight
