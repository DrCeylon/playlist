import ResonanceCore
import ResonanceDesign
import SwiftUI

struct ImportProgressView: View {
    let progress: ImportProgressSnapshot
    let manualPrompt: ManualAcquisitionPrompt?
    let architectErrorDetail: String?
    let onConfirmManual: () -> Void
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)

        VStack(alignment: .leading, spacing: 20) {
            Text("Import Apple Music")
                .font(.title2.weight(.semibold))
                .foregroundStyle(palette.textPrimary)

            if let manualPrompt {
                manualAcquisitionCard(prompt: manualPrompt, palette: palette)
            } else {
                ProgressView(value: progress.progressRatio)
                    .tint(palette.accentPrimary)

                if !progress.currentStep.isEmpty {
                    Text(progress.currentStep)
                        .font(.headline)
                        .foregroundStyle(palette.textPrimary)
                } else {
                    Text(phaseLabel(progress.phase))
                        .font(.headline)
                        .foregroundStyle(palette.textPrimary)
                }

                if !progress.currentTrackLabel.isEmpty {
                    Text(progress.currentTrackLabel)
                        .font(.callout)
                        .foregroundStyle(palette.textSecondary)
                }

                metricsRow(palette: palette)

                Text(progress.cancellationNote)
                    .font(.caption)
                    .foregroundStyle(palette.textTertiary)
            }

            if !progress.diagnostics.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Dernières étapes")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(palette.textSecondary)
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(Array(progress.diagnostics.enumerated()), id: \.offset) { _, line in
                            Text(line)
                                .font(.caption)
                                .foregroundStyle(palette.textTertiary)
                                .textSelection(.enabled)
                                .lineLimit(2)
                        }
                    }
                }
            }

            if ResonanceFeatureFlags.architectModeEnabled, let architectErrorDetail {
                Text(architectErrorDetail)
                    .font(.caption2.monospaced())
                    .foregroundStyle(palette.textTertiary)
                    .textSelection(.enabled)
            }
        }
        .padding(24)
    }

    @ViewBuilder
    private func metricsRow(palette: ThemePalette) -> some View {
        HStack(spacing: 10) {
            metricChip("Résolus", value: progress.resolvedCount, total: progress.totalTracks, palette: palette)
            metricChip("Ajoutés", value: progress.addedCount, palette: palette)
            metricChip("Introuv.", value: progress.notFoundCount, palette: palette)
            metricChip("Erreurs", value: progress.errorCount, palette: palette)
        }
    }

    private func metricChip(
        _ title: String,
        value: Int,
        total: Int? = nil,
        palette: ThemePalette
    ) -> some View {
        VStack(spacing: 2) {
            if let total {
                Text("\(value)/\(max(total, 1))")
                    .font(.caption.monospacedDigit().weight(.semibold))
            } else {
                Text("\(value)")
                    .font(.caption.monospacedDigit().weight(.semibold))
            }
            Text(title)
                .font(.caption2)
                .foregroundStyle(palette.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }

    @ViewBuilder
    private func manualAcquisitionCard(prompt: ManualAcquisitionPrompt, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Acquisition manuelle requise", systemImage: "music.note.list")
                .font(.headline)
                .foregroundStyle(palette.statusWarning)
            Text("\(prompt.artist) — \(prompt.title)")
                .font(.body.weight(.medium))
            if !prompt.catalogLabel.isEmpty {
                Text("Catalogue : \(prompt.catalogLabel)")
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
            }
            Text(prompt.instructions)
                .font(.callout)
                .foregroundStyle(palette.textSecondary)
            Button("J'ai ajouté le morceau, continuer", action: onConfirmManual)
                .buttonStyle(.borderedProminent)
                .tint(palette.accentPrimary)
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    private func phaseLabel(_ phase: ImportPhase) -> String {
        switch phase {
        case .resolving: return "Résolution des morceaux…"
        case .acquiring: return "Acquisition catalogue…"
        case .delivering: return "Ajout à la playlist Apple Music…"
        case .waitingForManualAcquisition: return "En attente d'ajout manuel"
        default: return "Import en cours…"
        }
    }
}
