import ResonanceCore
import ResonanceDesign
import SwiftUI

struct PlaylistPreviewView: View {
    let result: PlaylistGenerationResult
    let onEdit: () -> Void
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)

        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                VStack(alignment: .leading, spacing: 8) {
                    Text(result.playlistName)
                        .font(.largeTitle.weight(.semibold))
                        .foregroundStyle(palette.textPrimary)
                    Text("\(result.trackCount) morceaux · score moyen \(String(format: "%.2f", result.averageScore))")
                        .font(.callout)
                        .foregroundStyle(palette.textSecondary)
                    Text("Aperçu mock — prêt pour le Engine Bridge.")
                        .font(.caption)
                        .foregroundStyle(palette.textTertiary)
                }

                ForEach(result.sections) { section in
                    VStack(alignment: .leading, spacing: 10) {
                        Text(section.name)
                            .font(.headline)
                            .foregroundStyle(palette.textPrimary)
                        ForEach(section.tracks) { track in
                            HStack(alignment: .top, spacing: 12) {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(track.title)
                                        .font(.body)
                                        .foregroundStyle(palette.textPrimary)
                                    Text(track.artist)
                                        .font(.caption)
                                        .foregroundStyle(palette.textSecondary)
                                }
                                Spacer()
                                Text(String(format: "%.0f%%", track.score * 100))
                                    .font(.caption.monospacedDigit())
                                    .foregroundStyle(palette.accentPrimary)
                            }
                            .padding(.vertical, 6)
                            Divider().overlay(palette.borderSubtle)
                        }
                    }
                    .padding(16)
                    .background(palette.backgroundSecondary)
                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                }

                HStack {
                    Button("Modifier le formulaire", action: onEdit)
                        .buttonStyle(.bordered)
                    Spacer()
                    Label("Import non disponible (Phase 4.6)", systemImage: "square.and.arrow.down")
                        .font(.caption)
                        .foregroundStyle(palette.textTertiary)
                }
            }
            .padding(24)
        }
    }
}
