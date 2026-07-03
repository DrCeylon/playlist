import ResonanceCore
import ResonanceDesign
import SwiftUI

struct ImportOutcomeRow: View {
    let outcome: ImportTrackOutcome
    let palette: ThemePalette
    @State private var showsDetail = false
    @State private var copiedLabel: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: iconName)
                    .foregroundStyle(iconColor)
                    .frame(width: 18, alignment: .top)

                VStack(alignment: .leading, spacing: 4) {
                    SelectableText(
                        text: outcome.displayLabel,
                        font: .body.weight(.medium),
                        foreground: palette.textPrimary
                    )
                    if !outcome.album.isEmpty {
                        SelectableText(
                            text: outcome.album,
                            font: .caption,
                            foreground: palette.textSecondary
                        )
                    }
                    SelectableText(
                        text: statusLabel,
                        font: .caption.weight(.semibold),
                        foreground: iconColor
                    )
                    if !outcome.message.isEmpty {
                        SelectableText(
                            text: outcome.message,
                            font: .caption2,
                            foreground: palette.textTertiary
                        )
                    }
                }
                Spacer(minLength: 0)
            }

            HStack(spacing: 8) {
                actionButton("Copier", systemImage: "doc.on.doc") {
                    ClipboardSupport.copy(outcome.searchLine)
                    copiedLabel = "Copier"
                }
                if outcome.status == .acquiring || outcome.status == .notFound || outcome.status == .error {
                    actionButton("Ouvrir dans Music", systemImage: "music.note") {
                        openInMusic()
                    }
                }
                if !outcome.message.isEmpty {
                    actionButton(showsDetail ? "Masquer" : "Détail", systemImage: "info.circle") {
                        showsDetail.toggle()
                    }
                }
            }
            .controlSize(.small)

            if let copiedLabel {
                Text("Copié : \(copiedLabel)")
                    .font(.caption2)
                    .foregroundStyle(palette.statusSuccess)
            }

            if showsDetail, !outcome.message.isEmpty {
                CopyableField(label: "Détail", value: outcome.message, palette: palette)
            }
        }
        .padding(12)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }

    private var statusLabel: String {
        switch outcome.status {
        case .added: return "✓ Ajouté"
        case .skipped: return "Déjà présent"
        case .notFound: return "✗ Introuvable"
        case .error: return "✗ Erreur"
        case .acquiring: return "⚠ Acquisition manuelle"
        case .pending: return "En attente"
        }
    }

    private var iconName: String {
        ImportTrackActivityFormatter.iconName(status: outcome.status, step: .completed)
    }

    private var iconColor: Color {
        ImportTrackActivityFormatter.iconColor(status: outcome.status, step: .completed, palette: palette)
    }

    private func actionButton(_ title: String, systemImage: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Label(title, systemImage: systemImage)
        }
        .buttonStyle(.bordered)
    }

    private func openInMusic() {
        if !outcome.catalogURL.isEmpty {
            MusicAppLink.openURLString(outcome.catalogURL)
            return
        }
        MusicAppLink.openSearch(artist: outcome.artist, title: outcome.title, album: outcome.album)
    }
}
