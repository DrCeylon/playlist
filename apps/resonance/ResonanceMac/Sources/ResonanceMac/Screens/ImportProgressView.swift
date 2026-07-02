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

        BoundedScrollScreen {
            VStack(alignment: .leading, spacing: 20) {
                Text("Import Apple Music")
                    .font(.title2.weight(.semibold))
                    .foregroundStyle(palette.textPrimary)

                progressHeader(palette: palette)

                if let manualPrompt {
                    ManualAcquisitionCard(
                        prompt: manualPrompt,
                        trackPositionLabel: trackPositionLabel,
                        palette: palette,
                        onConfirmManual: onConfirmManual
                    )
                }

                if !progress.diagnostics.isEmpty {
                    diagnosticsSection(palette: palette)
                }

                if ResonanceFeatureFlags.architectModeEnabled, let architectErrorDetail {
                    Text(architectErrorDetail)
                        .font(.caption2.monospaced())
                        .foregroundStyle(palette.textTertiary)
                        .textSelection(.enabled)
                }
            }
            .padding(24)
            .frame(maxWidth: .infinity, alignment: .topLeading)
        }
    }

    @ViewBuilder
    private func progressHeader(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            ProgressView(value: progress.progressRatio)
                .tint(palette.accentPrimary)
                .animation(.easeInOut(duration: 0.25), value: progress.progressRatio)

            HStack(spacing: 8) {
                ProgressView()
                    .controlSize(.small)
                Text(activityLabel)
                    .font(.caption)
                    .foregroundStyle(palette.textTertiary)
            }

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
                    .textSelection(.enabled)
            }

            metricsRow(palette: palette)

            if manualPrompt == nil {
                Text(progress.cancellationNote)
                    .font(.caption)
                    .foregroundStyle(palette.textTertiary)
            }
        }
    }

    private var trackPositionLabel: String? {
        guard progress.totalTracks > 0 else { return nil }
        let index = min(progress.processedTracks + 1, progress.totalTracks)
        return "Morceau \(index) sur \(progress.totalTracks)"
    }

    private var activityLabel: String {
        let seconds = max(0, Int(Date().timeIntervalSince(progress.lastActivityAt)))
        if seconds <= 1 {
            return "Activité en cours…"
        }
        return "Dernière activité il y a \(seconds) s"
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
    private func diagnosticsSection(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Dernières étapes")
                .font(.caption.weight(.semibold))
                .foregroundStyle(palette.textSecondary)
            VStack(alignment: .leading, spacing: 4) {
                ForEach(progress.diagnostics, id: \.self) { line in
                    Text(line)
                        .font(.caption)
                        .foregroundStyle(palette.textTertiary)
                        .textSelection(.enabled)
                        .lineLimit(2)
                }
            }
        }
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
