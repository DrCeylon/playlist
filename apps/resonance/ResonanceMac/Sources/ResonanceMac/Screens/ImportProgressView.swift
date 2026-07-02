import ResonanceCore
import ResonanceDesign
import SwiftUI

struct ImportProgressView: View {
    let progress: ImportProgressSnapshot
    let manualPrompt: ManualAcquisitionPrompt?
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
                Text(phaseLabel(progress.phase))
                    .font(.headline)
                    .foregroundStyle(palette.textPrimary)
                if !progress.currentTrackLabel.isEmpty {
                    Text(progress.currentTrackLabel)
                        .font(.callout)
                        .foregroundStyle(palette.textSecondary)
                }
                Text("\(progress.processedTracks)/\(max(progress.totalTracks, 1)) morceaux")
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(palette.textTertiary)
            }

            if !progress.diagnostics.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Étapes")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(palette.textSecondary)
                    ForEach(Array(progress.diagnostics.enumerated()), id: \.offset) { _, line in
                        Text(line)
                            .font(.caption)
                            .foregroundStyle(palette.textTertiary)
                    }
                }
            }
        }
        .padding(24)
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
