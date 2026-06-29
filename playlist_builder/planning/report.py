from __future__ import annotations

from playlist_builder.planning.analyzer import PlaylistAnalysis, PlaylistAnalyzer
from playlist_builder.planning.models import GeneratedPlaylist


def build_mad_scientist_report(
    playlist: GeneratedPlaylist,
    *,
    analysis: PlaylistAnalysis | None = None,
) -> str:
    """Return a minimal, fun report for the future UI."""

    analysis = analysis or PlaylistAnalyzer().analyze(playlist)
    lines = [
        "🧪 Rapport du labo musical",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"Expérience : {playlist.request.name}",
        f"Résultat : {analysis.track_count} morceau(x) retenu(s)",
        f"Diversité artistes : {analysis.artist_count} artiste(s)",
        f"Score moyen : {analysis.average_score:.1f}",
    ]

    if analysis.average_energy is not None:
        lines.append(f"Énergie moyenne : {analysis.average_energy:.1f}/100")

    lines.extend(
        [
            f"Rejets contrôlés : {len(playlist.rejected)}",
            f"Suggestions en réserve : {len(playlist.suggestions)}",
            "",
            _format_top_artists(analysis),
            _format_taxonomy("Genres détectés", analysis.genres),
            _format_taxonomy("Humeurs détectées", analysis.moods),
            _format_taxonomy("Langues détectées", analysis.languages),
            "",
            "Conclusion du savant fou :",
            _conclusion(playlist),
        ]
    )
    return "\n".join(line for line in lines if line is not None)


def _format_top_artists(analysis: PlaylistAnalysis) -> str:
    if not analysis.top_artists:
        return "Artistes dominants : données insuffisantes"
    payload = ", ".join(f"{artist} ({count})" for artist, count in analysis.top_artists)
    return f"Artistes dominants : {payload}"


def _format_taxonomy(label: str, values: tuple[tuple[str, int], ...]) -> str:
    if not values:
        return f"{label} : données insuffisantes"
    payload = ", ".join(f"{value} ({count})" for value, count in values[:5])
    return f"{label} : {payload}"


def _conclusion(playlist: GeneratedPlaylist) -> str:
    if playlist.suggestions:
        return "Importer telle quelle, ou injecter quelques suggestions supplémentaires dans la mixture."
    if playlist.rejected:
        return "Importer telle quelle. Les exclusions ont été respectées, aucun monstre musical détecté."
    return "Importer telle quelle. La créature est stable et prête à danser."
