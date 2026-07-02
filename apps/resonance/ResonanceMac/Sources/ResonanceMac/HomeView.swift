import ResonanceCore
import ResonanceDesign
import SwiftUI

struct HomeView: View {
    @Binding var selection: SidebarItem?
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Bonjour")
                            .font(.largeTitle.weight(.semibold))
                            .foregroundStyle(palette.textPrimary)
                        Text("Génère, importe et retrouve tes playlists depuis une interface macOS.")
                            .font(.body)
                            .foregroundStyle(palette.textSecondary)
                    }

                    card(title: "Par où commencer", palette: palette) {
                        Text("Ouvre Nouvelle Playlist, saisis un nom et une graine musicale, puis génère et importe dans Apple Music.")
                            .font(.callout)
                            .foregroundStyle(palette.textSecondary)
                    }

                    card(title: "Raccourcis", palette: palette) {
                        HStack(spacing: 16) {
                            ForEach(HomeShortcut.allCases) { shortcut in
                                shortcutButton(shortcut, palette: palette)
                            }
                        }
                    }

                    card(title: "État", palette: palette) {
                        Text("Resonance — Preview produit Phase 4.8")
                            .font(.callout.weight(.medium))
                            .foregroundStyle(palette.textPrimary)
                        Text("Moteur Python provider-neutral, bridge runtime et historique local.")
                            .font(.callout)
                            .foregroundStyle(palette.textSecondary)
                    }
                }
                .padding(24)
            }
        }
        .navigationTitle("Accueil")
    }

    @ViewBuilder
    private func card<Content: View>(
        title: String,
        palette: ThemePalette,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
                .foregroundStyle(palette.textPrimary)
            content()
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }

    @ViewBuilder
    private func shortcutButton(_ shortcut: HomeShortcut, palette: ThemePalette) -> some View {
        Button {
            selection = shortcut.destination
        } label: {
            VStack(spacing: 8) {
                Image(systemName: shortcut.systemImage)
                    .font(.title2)
                Text(shortcut.title)
                    .font(.caption)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(palette.backgroundElevated, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
            .foregroundStyle(palette.accentPrimary)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(shortcut.title)
    }
}
