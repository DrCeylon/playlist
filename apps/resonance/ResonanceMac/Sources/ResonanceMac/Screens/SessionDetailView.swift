import ResonanceCore
import ResonanceDesign
import SwiftUI

struct SessionDetailView: View {
    let detail: SessionHistoryDetail?
    let canReplay: Bool
    let canReimport: Bool
    let replayDisabledReason: String?
    let reimportDisabledReason: String?
    let onReplay: () -> Void
    let onReimport: () -> Void
    let onExport: () -> Void
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)
        VStack(alignment: .leading, spacing: 12) {
            Text("Détail session")
                .font(.headline)
                .foregroundStyle(palette.textPrimary)

            if let detail {
                Text(detail.summary.playlistName)
                    .font(.title3.weight(.semibold))
                    .foregroundStyle(palette.textPrimary)
                Text("Statut : \(detail.summary.status.rawValue)")
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)

                importMetrics(for: detail, palette: palette)
                importOutcomeList(for: detail, palette: palette)

                Group {
                    Text("Requête : \(detail.generationRequest.isEmpty ? "—" : "disponible")")
                    Text("Preview : \(detail.generationResult.isEmpty ? "—" : "disponible")")
                    Text("Import : \(detail.importResult.isEmpty ? "—" : "disponible")")
                    Text("Rapport texte : \(detail.summary.textReportPath.isEmpty ? "—" : detail.summary.textReportPath)")
                    Text("Rapport JSON : \(detail.summary.jsonReportPath.isEmpty ? "—" : detail.summary.jsonReportPath)")
                }
                .font(.caption)
                .foregroundStyle(palette.textSecondary)

                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Button("Relancer génération", action: onReplay)
                            .buttonStyle(.borderedProminent)
                            .tint(palette.accentPrimary)
                            .disabled(!canReplay)
                        Button("Réimporter", action: onReimport)
                            .buttonStyle(.bordered)
                            .disabled(!canReimport)
                        Button("Exporter", action: onExport)
                            .buttonStyle(.bordered)
                    }
                    if let replayDisabledReason, !canReplay {
                        Text(replayDisabledReason)
                            .font(.caption2)
                            .foregroundStyle(palette.statusWarning)
                    }
                    if let reimportDisabledReason, !canReimport {
                        Text(reimportDisabledReason)
                            .font(.caption2)
                            .foregroundStyle(palette.statusWarning)
                    }
                }
            } else {
                Text("Sélectionne une session pour afficher les détails.")
                    .foregroundStyle(palette.textSecondary)
            }
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }

    @ViewBuilder
    private func importMetrics(for detail: SessionHistoryDetail, palette: ThemePalette) -> some View {
        HStack(spacing: 8) {
            metric("Ajoutés", value: detail.summary.addedCount, palette: palette)
            metric("Ignorés", value: detail.summary.skippedCount, palette: palette)
            metric("Introuv.", value: detail.summary.notFoundCount, palette: palette)
            metric("Erreurs", value: detail.summary.errorCount, palette: palette)
        }
    }

    private func metric(_ title: String, value: Int, palette: ThemePalette) -> some View {
        VStack(spacing: 2) {
            Text("\(value)")
                .font(.caption.monospacedDigit().weight(.semibold))
            Text(title)
                .font(.caption2)
        }
        .frame(maxWidth: .infinity)
        .padding(6)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    @ViewBuilder
    private func importOutcomeList(for detail: SessionHistoryDetail, palette: ThemePalette) -> some View {
        let outcomes = HistoryPayloadMapper.importOutcomes(from: detail.importResult)
        let nonAdded = outcomes.filter { $0.status != .added }
        if !nonAdded.isEmpty {
            VStack(alignment: .leading, spacing: 6) {
                Text("Morceaux non ajoutés")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(palette.statusWarning)
                ForEach(nonAdded) { outcome in
                    VStack(alignment: .leading, spacing: 2) {
                        Text("\(outcome.artist) — \(outcome.title)")
                            .font(.caption)
                        Text(outcomeLabel(outcome))
                            .font(.caption2)
                            .foregroundStyle(palette.textTertiary)
                    }
                }
            }
        }
    }

    private func outcomeLabel(_ outcome: ImportTrackOutcome) -> String {
        let status: String
        switch outcome.status {
        case .skipped: status = "Déjà présent / ignoré"
        case .notFound: status = "Non trouvé dans Apple Music"
        case .error: status = "Erreur"
        default: status = outcome.status.rawValue
        }
        if outcome.message.isEmpty {
            return status
        }
        return "\(status) — \(outcome.message)"
    }
}
