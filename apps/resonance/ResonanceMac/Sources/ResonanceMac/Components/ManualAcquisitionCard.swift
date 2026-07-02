import AppKit
import ResonanceCore
import ResonanceDesign
import SwiftUI

struct ManualAcquisitionCard: View {
    let prompt: ManualAcquisitionPrompt
    let trackPositionLabel: String?
    let palette: ThemePalette
    let onConfirmManual: () -> Void
    @State private var copiedLabel: String?

    private var searchLine: String {
        let artist = prompt.artist.trimmingCharacters(in: .whitespacesAndNewlines)
        let title = prompt.title.trimmingCharacters(in: .whitespacesAndNewlines)
        if artist.isEmpty { return title }
        if title.isEmpty { return artist }
        return "\(artist) — \(title)"
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Label("Acquisition manuelle requise", systemImage: "music.note.list")
                .font(.headline)
                .foregroundStyle(palette.statusWarning)

            if let trackPositionLabel {
                Text(trackPositionLabel)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(palette.textSecondary)
            }

            Text(searchLine)
                .font(.title3.weight(.semibold))
                .foregroundStyle(palette.textPrimary)
                .textSelection(.enabled)

            if !prompt.catalogLabel.isEmpty {
                Text("Catalogue : \(prompt.catalogLabel)")
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
                    .textSelection(.enabled)
            }

            Text(prompt.instructions)
                .font(.callout)
                .foregroundStyle(palette.textSecondary)
                .textSelection(.enabled)

            copyActions

            if let copiedLabel {
                Text("Copié : \(copiedLabel)")
                    .font(.caption2)
                    .foregroundStyle(palette.statusSuccess)
            }

            HStack(spacing: 10) {
                Button("Ouvrir Music.app") {
                    ClipboardSupport.openMusicApp()
                }
                .buttonStyle(.bordered)

                Button("J'ai ajouté le morceau, continuer", action: onConfirmManual)
                    .buttonStyle(.borderedProminent)
                    .tint(palette.accentPrimary)
            }
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    private var copyActions: some View {
        HStack(spacing: 8) {
            copyButton("Copier recherche", value: searchLine)
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
}
