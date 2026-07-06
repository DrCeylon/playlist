import AppKit
import ResonanceCore
import ResonanceDesign
import SwiftUI

struct ManualAcquisitionCard: View {
    let prompt: ManualAcquisitionPrompt
    let trackPositionLabel: String?
    let pollStatus: String
    let isContinueInProgress: Bool
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

            if !pollStatus.isEmpty {
                HStack(spacing: 8) {
                    ProgressView()
                        .controlSize(.small)
                    SelectableText(
                        text: pollStatus,
                        font: .caption,
                        foreground: palette.textSecondary
                    )
                }
            }

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

            Text("Resonance vérifie automatiquement la bibliothèque toutes les quelques secondes et reprend l'import dès que le morceau est détecté.")
                .font(.caption)
                .foregroundStyle(palette.textSecondary)
                .textSelection(.enabled)
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
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
