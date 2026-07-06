import AppKit
import ResonanceCore
import ResonanceDesign
import SwiftUI

struct ManualAcquisitionCard: View {
    let prompt: ManualAcquisitionPrompt
    let trackPositionLabel: String?
    let status: ManualAcquisitionUIStatus
    let isContinueInProgress: Bool
    let architectDiagnostics: String?
    let palette: ThemePalette
    let onConfirmManual: () -> Void
    @State private var copiedLabel: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Label("Acquisition manuelle requise", systemImage: "music.note.list")
                .font(.headline)
                .foregroundStyle(palette.statusWarning)

            if let trackPositionLabel {
                SelectableText(
                    text: trackPositionLabel,
                    font: .caption.weight(.semibold),
                    foreground: palette.textSecondary
                )
            }

            CopyableField(label: "Morceau", value: prompt.searchLine, palette: palette)

            if !prompt.album.isEmpty {
                CopyableField(label: "Album", value: prompt.album, palette: palette)
            }

            if !prompt.catalogLabel.isEmpty {
                CopyableField(label: "Catalogue", value: prompt.catalogLabel, palette: palette)
            }

            SelectableText(
                text: prompt.instructions,
                font: .callout,
                foreground: palette.textSecondary
            )

            copyActions

            if let copiedLabel {
                Text("Copié : \(copiedLabel)")
                    .font(.caption2)
                    .foregroundStyle(palette.statusSuccess)
            }

            verificationStatusSection

            HStack(spacing: 10) {
                Button("Ouvrir dans Music") {
                    openInMusic()
                }
                .buttonStyle(.bordered)

                Button("J'ai ajouté le morceau, continuer", action: onConfirmManual)
                    .buttonStyle(.borderedProminent)
                    .tint(palette.accentPrimary)
                    .disabled(isContinueInProgress)
            }

            Text("Music.app ne s'ouvre que si vous touchez « Ouvrir dans Music ». Resonance ne reprend plus le focus automatiquement.")
                .font(.caption.weight(.semibold))
                .foregroundStyle(palette.textPrimary)

            Text("Ajoutez le morceau à votre bibliothèque dans Music.app, puis cliquez sur « J'ai ajouté le morceau, continuer ». Resonance vérifiera alors la bibliothèque et reprendra l'import si le morceau est détecté. Resonance peut aussi détecter automatiquement le morceau en arrière-plan, mais le bouton permet de relancer immédiatement la vérification.")
                .font(.caption)
                .foregroundStyle(palette.textSecondary)
                .textSelection(.enabled)

            if ResonanceFeatureFlags.architectModeEnabled, let architectDiagnostics, !architectDiagnostics.isEmpty {
                SelectableText(
                    text: architectDiagnostics,
                    font: .caption2.monospaced(),
                    foreground: palette.textSecondary
                )
            }
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    @ViewBuilder
    private var verificationStatusSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            statusRow(title: "Phase", value: status.phase.userFacingStep)
            if let elapsed = status.elapsedSincePhaseEnteredLabel {
                statusRow(title: "Temps écoulé", value: elapsed)
            }
            if let clickLabel = status.lastUserClickLabel {
                statusRow(title: "Dernier clic", value: "Vérification lancée à \(clickLabel)")
            }
            if !status.currentStep.isEmpty {
                HStack(spacing: 8) {
                    if isContinueInProgress {
                        ProgressView()
                            .controlSize(.small)
                    }
                    statusRow(title: "Action en cours", value: status.currentStep)
                }
            }
            if !status.lastVerificationResult.isEmpty {
                statusRow(title: "Dernier résultat", value: status.lastVerificationResult)
            }
            if !status.nextStepHint.isEmpty {
                statusRow(title: "Prochaine étape", value: status.nextStepHint)
            }
        }
        .padding(12)
        .background(palette.backgroundPrimary.opacity(0.55))
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }

    private func statusRow(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title)
                .font(.caption2.weight(.semibold))
                .foregroundStyle(palette.textSecondary)
            SelectableText(
                text: value,
                font: .caption,
                foreground: palette.textPrimary
            )
        }
    }

    private var copyActions: some View {
        HStack(spacing: 8) {
            copyButton("Copier recherche", value: prompt.searchLine)
            copyButton("Artiste", value: prompt.artist)
            copyButton("Morceau", value: prompt.title)
        }
    }

    private func copyButton(_ title: String, value: String) -> some View {
        Button(title) {
            ClipboardSupport.copy(value)
            copiedLabel = title
        }
        .buttonStyle(.bordered)
        .controlSize(.small)
        .disabled(value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
    }

    private func openInMusic() {
        if !prompt.catalogURL.isEmpty {
            MusicAppLink.openURLString(prompt.catalogURL)
            return
        }
        MusicAppLink.openSearch(artist: prompt.artist, title: prompt.title, album: prompt.album)
    }
}
