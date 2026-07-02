import ResonanceCore
import ResonanceDesign
import SwiftUI

struct SessionDetailView: View {
    let detail: SessionHistoryDetail?
    let canReplay: Bool
    let canReimport: Bool
    let isBusy: Bool
    let replayDescription: String
    let reimportDescription: String
    let exportDescription: String
    let replayDisabledReason: String?
    let reimportDisabledReason: String?
    let onReplay: () -> Void
    let onReimport: () -> Void
    let onExport: () -> Void
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)
        BoundedScrollScreen {
            VStack(alignment: .leading, spacing: 12) {
                Text("Détail session")
                    .font(.headline)
                    .foregroundStyle(palette.textPrimary)

                if let detail {
                    Text(detail.summary.playlistName)
                        .font(.title3.weight(.semibold))
                        .foregroundStyle(palette.textPrimary)
                    Text("Statut : \(statusLabel(detail.summary.status))")
                        .font(.caption)
                        .foregroundStyle(palette.textSecondary)

                    importMetrics(for: detail, palette: palette)
                    importOutcomeList(for: detail, palette: palette)

                    availabilitySection(for: detail, palette: palette)
                    actionsSection(palette: palette)
                } else {
                    Text("Sélectionne une session pour afficher les détails.")
                        .foregroundStyle(palette.textSecondary)
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .topLeading)
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }

    @ViewBuilder
    private func availabilitySection(for detail: SessionHistoryDetail, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Données disponibles")
                .font(.caption.weight(.semibold))
                .foregroundStyle(palette.textSecondary)
            Text("Requête : \(detail.generationRequest.isEmpty ? "indisponible" : "enregistrée")")
            Text("Preview : \(detail.generationResult.isEmpty ? "indisponible" : "enregistrée")")
            Text("Import : \(detail.importResult.isEmpty ? "non exécuté" : "rapport enregistré")")
            if !detail.summary.jsonReportPath.isEmpty {
                Text("Rapport JSON : \(detail.summary.jsonReportPath)")
            } else if !detail.summary.textReportPath.isEmpty {
                Text("Rapport texte : \(detail.summary.textReportPath)")
            } else {
                Text("Rapport fichier : non généré sur disque")
            }
        }
        .font(.caption)
        .foregroundStyle(palette.textTertiary)
        .textSelection(.enabled)
    }

    @ViewBuilder
    private func actionsSection(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Actions")
                .font(.subheadline.weight(.semibold))

            actionRow(
                title: "Relancer génération",
                description: replayDescription,
                disabledReason: replayDisabledReason,
                isEnabled: canReplay && !isBusy,
                palette: palette,
                action: onReplay,
                isPrimary: true
            )

            actionRow(
                title: "Réimporter dans Apple Music",
                description: reimportDescription,
                disabledReason: reimportDisabledReason,
                isEnabled: canReimport && !isBusy,
                palette: palette,
                action: onReimport,
                isPrimary: false
            )

            actionRow(
                title: "Exporter le rapport",
                description: exportDescription,
                disabledReason: detail == nil ? "Sélectionne une session." : nil,
                isEnabled: detail != nil && !isBusy,
                palette: palette,
                action: onExport,
                isPrimary: false
            )
        }
    }

    private func actionRow(
        title: String,
        description: String,
        disabledReason: String?,
        isEnabled: Bool,
        palette: ThemePalette,
        action: @escaping () -> Void,
        isPrimary: Bool
    ) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Button(title, action: action)
                .buttonStyle(isPrimary ? .borderedProminent : .bordered)
                .tint(isPrimary ? palette.accentPrimary : nil)
                .disabled(!isEnabled)
            Text(description)
                .font(.caption)
                .foregroundStyle(palette.textSecondary)
            if let disabledReason, !isEnabled {
                Text(disabledReason)
                    .font(.caption2)
                    .foregroundStyle(palette.statusWarning)
            }
        }
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
                            .textSelection(.enabled)
                        Text(outcomeLabel(outcome))
                            .font(.caption2)
                            .foregroundStyle(palette.textTertiary)
                    }
                }
            }
        }
    }

    private func statusLabel(_ status: SessionHistoryStatus) -> String {
        switch status {
        case .generated: return "Générée"
        case .imported: return "Importée"
        case .partialSuccess: return "Import partiel"
        case .failed: return "Échouée"
        case .waitingForManualAcquisition: return "Ajout manuel requis"
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
