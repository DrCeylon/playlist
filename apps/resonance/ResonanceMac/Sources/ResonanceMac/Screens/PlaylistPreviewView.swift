import ResonanceCore
import ResonanceDesign
import SwiftUI

struct PlaylistPreviewView: View {
    let result: PlaylistGenerationResult
    let previewSourceLabel: String
    let onEdit: () -> Void
    let onImport: () -> Void
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)

        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                VStack(alignment: .leading, spacing: 8) {
                    Text(result.playlistName)
                        .font(.largeTitle.weight(.semibold))
                        .foregroundStyle(palette.textPrimary)
                    Text("\(result.trackCount) morceaux · score moyen \(scoreLabel(result.averageScore))")
                        .font(.callout)
                        .foregroundStyle(palette.textSecondary)
                    Text(previewSourceLabel)
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
                                Text(scoreLabel(track.score))
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
                    Button(action: onImport) {
                        Label("Importer dans Apple Music", systemImage: "square.and.arrow.down")
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(palette.accentPrimary)
                }
            }
            .padding(24)
        }
    }

    private func scoreLabel(_ score: Double) -> String {
        let percent = score > 1.0 ? score : score * 100
        return String(format: "%.0f%%", percent)
    }
}
