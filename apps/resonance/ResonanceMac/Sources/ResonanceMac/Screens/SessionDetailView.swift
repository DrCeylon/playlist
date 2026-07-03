import ResonanceCore
import ResonanceDesign
import SwiftUI

struct SessionDetailView: View {
    let detail: SessionHistoryDetail?
    let canView: Bool
    let canEdit: Bool
    let canImport: Bool
    let canRetry: Bool
    let isBusy: Bool
    let viewDescription: String
    let editDescription: String
    let importDescription: String
    let retryDescription: String
    let exportDescription: String
    let viewDisabledReason: String?
    let editDisabledReason: String?
    let importDisabledReason: String?
    let retryDisabledReason: String?
    let onView: () -> Void
    let onEdit: () -> Void
    let onImport: () -> Void
    let onRetry: () -> Void
    let onExport: () -> Void
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)
        BoundedScrollScreen {
            VStack(alignment: .leading, spacing: 12) {
                Text("Reprendre le workflow")
                    .font(.headline)
                    .foregroundStyle(palette.textPrimary)

                if let detail {
                    Text(detail.summary.playlistName)
                        .font(.title3.weight(.semibold))
                        .foregroundStyle(palette.textPrimary)
                    statusBadge(for: detail.summary.status, palette: palette)
                    Text(SessionHistoryDisplay.rowSubtitle(for: detail.summary))
                        .font(.callout)
                        .foregroundStyle(palette.textSecondary)

                    importMetrics(for: detail, palette: palette)
                    importOutcomeList(for: detail, palette: palette)
                    primaryActionsSection(palette: palette)

                    if ResonanceFeatureFlags.architectModeEnabled {
                        architectSection(for: detail, palette: palette)
                    }
                } else {
                    Text("Sélectionne une session pour afficher les actions disponibles.")
                        .foregroundStyle(palette.textSecondary)
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .topLeading)
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }

    @ViewBuilder
    private func statusBadge(for status: SessionHistoryStatus, palette: ThemePalette) -> some View {
        Text(SessionHistoryDisplay.statusLabel(for: status))
            .font(.caption.weight(.semibold))
            .padding(.horizontal, 10)
            .padding(.vertical, 4)
            .background(badgeBackground(for: status, palette: palette))
            .foregroundStyle(badgeForeground(for: status, palette: palette))
            .clipShape(Capsule())
    }

    @ViewBuilder
    private func primaryActionsSection(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            actionRow(
                title: "Voir la playlist",
                description: viewDescription,
                disabledReason: viewDisabledReason,
                isEnabled: canView && !isBusy,
                palette: palette,
                action: onView,
                isPrimary: true
            )

            actionRow(
                title: "Modifier cette playlist",
                description: editDescription,
                disabledReason: editDisabledReason,
                isEnabled: canEdit && !isBusy,
                palette: palette,
                action: onEdit,
                isPrimary: false
            )

            actionRow(
                title: "Importer",
                description: importDescription,
                disabledReason: importDisabledReason,
                isEnabled: canImport && !isBusy,
                palette: palette,
                action: onImport,
                isPrimary: false
            )

            actionRow(
                title: "Réessayer",
                description: retryDescription,
                disabledReason: retryDisabledReason,
                isEnabled: canRetry && !isBusy,
                palette: palette,
                action: onRetry,
                isPrimary: false
            )
        }
    }

    @ViewBuilder
    private func architectSection(for detail: SessionHistoryDetail, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Diagnostic")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(palette.textSecondary)

            VStack(alignment: .leading, spacing: 4) {
                Text("Requête : \(detail.generationRequest.isEmpty ? "indisponible" : "enregistrée")")
                Text("Preview : \(detail.generationResult.isEmpty ? "indisponible" : "enregistrée")")
                Text("Import : \(detail.importResult.isEmpty ? "non exécuté" : "rapport enregistré")")
            }
            .font(.caption)
            .foregroundStyle(palette.textSecondary)
            .textSelection(.enabled)

            actionRow(
                title: "Exporter",
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
            if isPrimary {
                Button(title, action: action)
                    .buttonStyle(.borderedProminent)
                    .tint(palette.accentPrimary)
                    .disabled(!isEnabled)
            } else {
                Button(title, action: action)
                    .buttonStyle(.bordered)
                    .disabled(!isEnabled)
            }
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
        if detail.summary.addedCount > 0
            || detail.summary.skippedCount > 0
            || detail.summary.notFoundCount > 0
            || detail.summary.errorCount > 0 {
            HStack(spacing: 8) {
                metric("Ajoutés", value: detail.summary.addedCount, palette: palette)
                metric("Ignorés", value: detail.summary.skippedCount, palette: palette)
                metric("Introuv.", value: detail.summary.notFoundCount, palette: palette)
                metric("Erreurs", value: detail.summary.errorCount, palette: palette)
            }
        }
    }

    private func metric(_ title: String, value: Int, palette: ThemePalette) -> some View {
        VStack(spacing: 2) {
            Text("\(value)")
                .font(.caption.monospacedDigit().weight(.semibold))
                .foregroundStyle(palette.textPrimary)
            Text(title)
                .font(.caption2)
                .foregroundStyle(palette.textSecondary)
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
                            .foregroundStyle(palette.textPrimary)
                            .textSelection(.enabled)
                        Text(outcomeLabel(outcome))
                            .font(.caption2)
                            .foregroundStyle(palette.textSecondary)
                    }
                }
            }
        }
    }

    private func badgeBackground(for status: SessionHistoryStatus, palette: ThemePalette) -> Color {
        switch status {
        case .generated: return palette.accentPrimary.opacity(0.15)
        case .imported: return palette.statusSuccess.opacity(0.15)
        case .partialSuccess, .waitingForManualAcquisition: return palette.statusWarning.opacity(0.15)
        case .failed: return palette.statusError.opacity(0.15)
        }
    }

    private func badgeForeground(for status: SessionHistoryStatus, palette: ThemePalette) -> Color {
        switch status {
        case .generated: return palette.accentPrimary
        case .imported: return palette.statusSuccess
        case .partialSuccess, .waitingForManualAcquisition: return palette.statusWarning
        case .failed: return palette.statusError
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
