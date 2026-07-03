import ResonanceCore
import ResonanceDesign
import SwiftUI

struct PlaylistPreviewView: View {
    let result: PlaylistGenerationResult
    let previewSourceLabel: String
    var showsWorkflowActions: Bool = true
    var onEdit: () -> Void = {}
    var onImport: () -> Void = {}
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)

        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                VStack(alignment: .leading, spacing: 8) {
                    Text(result.playlistName)
                        .font(.largeTitle.weight(.semibold))
                        .foregroundStyle(palette.textPrimary)
                    Text("\(result.trackCount) morceaux · \(TrackConfidenceDisplay.averageLabel(for: result.averageScore))")
                        .font(.callout)
                        .foregroundStyle(palette.textSecondary)
                    Text("Chaque morceau est classé selon sa pertinence par rapport à votre demande.")
                        .font(.caption)
                        .foregroundStyle(palette.textSecondary)
                    Text(previewSourceLabel)
                        .font(.caption)
                        .foregroundStyle(palette.textSecondary)
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
                                Text(TrackConfidenceDisplay.label(for: track.score))
                                    .font(.caption.weight(.medium))
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

                if showsWorkflowActions {
                    HStack(spacing: 12) {
                        Button(action: onEdit) {
                            Label("Modifier le formulaire", systemImage: "pencil")
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(palette.accentSecondary)
                        .controlSize(.large)

                        Spacer()

                        Button(action: onImport) {
                            Label("Importer", systemImage: "square.and.arrow.down")
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(palette.accentPrimary)
                        .controlSize(.large)
                    }
                }
            }
            .padding(24)
        }
    }
}
