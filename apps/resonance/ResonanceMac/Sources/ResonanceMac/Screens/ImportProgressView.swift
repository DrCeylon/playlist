import ResonanceCore
import ResonanceDesign
import SwiftUI

struct ImportProgressView: View {
    let progress: ImportProgressSnapshot
    let manualPrompt: ManualAcquisitionPrompt?
    let manualPollStatus: String
    let architectErrorDetail: String?
    let embeddedInPanel: Bool
    let onConfirmManual: () -> Void
    @EnvironmentObject private var themeManager: ThemeManager

    init(
        progress: ImportProgressSnapshot,
        manualPrompt: ManualAcquisitionPrompt?,
        manualPollStatus: String,
        architectErrorDetail: String?,
        embeddedInPanel: Bool = false,
        onConfirmManual: @escaping () -> Void
    ) {
        self.progress = progress
        self.manualPrompt = manualPrompt
        self.manualPollStatus = manualPollStatus
        self.architectErrorDetail = architectErrorDetail
        self.embeddedInPanel = embeddedInPanel
        self.onConfirmManual = onConfirmManual
    }

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)

        Group {
            if embeddedInPanel {
                content(palette: palette)
            } else {
                BoundedScrollScreen {
                    content(palette: palette)
                }
                .themedSurfaceCard(fill: palette.surface.opacity(0.98), border: palette.borderSubtle)
            }
        }
    }

    @ViewBuilder
    private func content(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Import Apple Music")
                .font(.title2.weight(.semibold))
                .foregroundStyle(palette.textPrimary)

            progressHeader(palette: palette)

            if !progress.activities.isEmpty {
                activityFeed(palette: palette)
            }

            if let manualPrompt {
                ManualAcquisitionCard(
                    prompt: manualPrompt,
                    trackPositionLabel: trackPositionLabel,
                    pollStatus: manualPollStatus,
                    palette: palette,
                    onConfirmManual: onConfirmManual
                )
            }

            if !progress.diagnostics.isEmpty {
                diagnosticsSection(palette: palette)
            }

            if ResonanceFeatureFlags.architectModeEnabled, let architectErrorDetail {
                SelectableText(
                    text: architectErrorDetail,
                    font: .caption2.monospaced(),
                    foreground: palette.textSecondary
                )
            }
        }
        .padding(embeddedInPanel ? 0 : 24)
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }

    @ViewBuilder
    private func progressHeader(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            ProgressView(value: max(0.02, progress.progressRatio))
                .tint(palette.accentPrimary)
                .animation(.easeInOut(duration: 0.25), value: progress.progressRatio)

            Text(progress.phaseLabel)
                .font(.caption.weight(.semibold))
                .foregroundStyle(palette.textPrimary)

            if !progress.remainingTracksLabel.isEmpty {
                Text(progress.remainingTracksLabel)
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
            }

            HStack(spacing: 8) {
                ProgressView()
                    .controlSize(.small)
                Text(activityLabel)
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
            }

            if !progress.currentStep.isEmpty {
                SelectableText(
                    text: progress.currentStep,
                    font: .headline,
                    foreground: palette.textPrimary
                )
            } else {
                SelectableText(
                    text: phaseLabel(progress.phase),
                    font: .headline,
                    foreground: palette.textPrimary
                )
            }

            if !progress.currentTrackLabel.isEmpty {
                SelectableText(
                    text: progress.currentTrackLabel,
                    font: .callout,
                    foreground: palette.textSecondary
                )
            }

            ImportMetricsRow(
                resolved: progress.totalTracks > 0 ? progress.processedTracks : nil,
                resolvedTotal: progress.totalTracks > 0 ? progress.totalTracks : nil,
                added: progress.addedCount,
                skipped: progress.skippedCount,
                notFound: progress.notFoundCount,
                errors: progress.errorCount,
                palette: palette
            )

            if manualPrompt == nil {
                SelectableText(
                    text: progress.cancellationNote,
                    font: .caption,
                    foreground: palette.textSecondary
                )
            }
        }
        .padding(16)
        .background(palette.backgroundSecondary.opacity(embeddedInPanel ? 0.72 : 0.94))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    @ViewBuilder
    private func activityFeed(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Progression morceau par morceau")
                .font(.caption.weight(.semibold))
                .foregroundStyle(palette.textPrimary)
            VStack(alignment: .leading, spacing: 0) {
                ForEach(progress.activities) { activity in
                    ImportTrackActivityRow(activity: activity, palette: palette)
                }
            }
            .padding(12)
            .background(palette.backgroundSecondary.opacity(0.94))
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
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
    private func diagnosticsSection(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Dernières étapes")
                .font(.caption.weight(.semibold))
                .foregroundStyle(palette.textPrimary)
            VStack(alignment: .leading, spacing: 4) {
                ForEach(progress.diagnostics, id: \.self) { line in
                    SelectableText(
                        text: line,
                        font: .caption,
                        foreground: palette.textSecondary,
                        lineLimit: 3
                    )
                }
            }
            .padding(12)
            .background(palette.backgroundSecondary.opacity(0.94))
            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
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
