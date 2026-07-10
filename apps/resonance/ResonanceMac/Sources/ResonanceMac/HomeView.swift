import ResonanceCore
import ResonanceDesign
import SwiftUI

struct HomeView: View {
    @Binding var selection: SidebarItem?
    @EnvironmentObject private var themeManager: ThemeManager
    @EnvironmentObject private var workflow: AppWorkflowCoordinator
    @StateObject private var playlistsModel = PlaylistsViewModel(service: MockPlaylistLibraryService())

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Bonjour")
                            .font(.largeTitle.weight(.semibold))
                            .foregroundStyle(palette.textPrimary)
                        Text("Gère, synchronise et retrouve tes playlists depuis un tableau de bord macOS.")
                            .font(.body)
                            .foregroundStyle(palette.textSecondary)
                    }

                    card(title: "Playlists récentes", palette: palette) {
                        if playlistsModel.recentPlaylists.isEmpty {
                            Text("Aucune playlist locale pour le moment — génère ou importe une première playlist.")
                                .font(.callout)
                                .foregroundStyle(palette.textSecondary)
                        } else {
                            VStack(alignment: .leading, spacing: 8) {
                                ForEach(playlistsModel.recentPlaylists) { playlist in
                                    HStack {
                                        VStack(alignment: .leading, spacing: 2) {
                                            Text(playlist.name)
                                                .font(.callout.weight(.semibold))
                                            Text("\(PlaylistLibraryDisplay.providerLabel(playlist.providerID)) · \(playlist.trackCount) morceaux")
                                                .font(.caption)
                                                .foregroundStyle(palette.textSecondary)
                                        }
                                        Spacer()
                                        Text(PlaylistLibraryDisplay.syncStatusLabel(playlist.syncStatus))
                                            .font(.caption2)
                                            .foregroundStyle(palette.accentPrimary)
                                    }
                                }
                                Button("Voir toutes les playlists") { selection = .playlists }
                                    .buttonStyle(.bordered)
                            }
                        }
                    }

                    card(title: "Actions rapides", palette: palette) {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack(spacing: 16) {
                                ForEach(HomeShortcut.allCases) { shortcut in
                                    shortcutButton(shortcut, palette: palette)
                                }
                            }
                            if let blockingLabel = workflow.processBlockingLabel {
                                Label(blockingLabel, systemImage: "hourglass")
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(palette.statusWarning)
                            }
                        }
                    }

                    card(title: "Reprise de workflow", palette: palette) {
                        VStack(alignment: .leading, spacing: 8) {
                            Button("Historique des sessions") { selection = .history }
                                .buttonStyle(.bordered)
                            Button("Synchronisation provider") { selection = .sync }
                                .buttonStyle(.bordered)
                            Text("Reprends un import partiel, une acquisition manuelle ou une synchronisation en attente.")
                                .font(.caption)
                                .foregroundStyle(palette.textSecondary)
                        }
                    }

                    card(title: "État", palette: palette) {
                        Text("Resonance 1.0.0")
                            .font(.callout.weight(.medium))
                            .foregroundStyle(palette.textPrimary)
                        Text("Architecture provider-neutral, Apple Music principal, YouTube Music expérimental.")
                            .font(.callout)
                            .foregroundStyle(palette.textSecondary)
                    }
                }
                .padding(24)
            }
        }
        .navigationTitle("Accueil")
        .task {
            playlistsModel.replaceService(workflow.engineBridge)
            await playlistsModel.refresh()
        }
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
        let blocked = shortcut.triggersWorkflow && !workflow.canStartProcess()
        Button {
            guard !blocked else { return }
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
            .foregroundStyle(blocked ? palette.textSecondary : palette.accentPrimary)
        }
        .buttonStyle(.plain)
        .disabled(blocked)
        .opacity(blocked ? 0.55 : 1)
        .accessibilityLabel(shortcut.title)
    }
}
