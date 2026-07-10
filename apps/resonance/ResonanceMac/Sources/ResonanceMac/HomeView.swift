import ResonanceCore
import ResonanceDesign
import SwiftUI

struct HomeView: View {
    @Binding var selection: SidebarItem?
    @EnvironmentObject private var themeManager: ThemeManager
    @EnvironmentObject private var workflow: AppWorkflowCoordinator

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    header(palette: palette)

                    if !workflow.libraryStore.playlistsNeedingAttention.isEmpty {
                        attentionCard(palette: palette)
                    }

                    ProductSectionCard(title: "Playlists récentes", palette: palette) {
                        recentPlaylistsSection(palette: palette)
                    }

                    ProductSectionCard(title: "Actions rapides", palette: palette) {
                        quickActionsSection(palette: palette)
                    }

                    if workflow.banner != nil || workflow.isProcessRunning {
                        ProductSectionCard(title: "En cours", palette: palette) {
                            VStack(alignment: .leading, spacing: 8) {
                                Button("Reprendre le travail en cours") {
                                    selection = workflow.activeRoute
                                }
                                .buttonStyle(.borderedProminent)
                                Text("Génération, import ou synchronisation — reprends là où tu t'étais arrêté.")
                                    .font(.caption)
                                    .foregroundStyle(palette.textSecondary)
                            }
                        }
                    }
                }
                .padding(24)
            }
        }
        .navigationTitle("Accueil")
        .refreshable {
            await workflow.libraryStore.refresh()
        }
    }

    @ViewBuilder
    private func header(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Bonjour")
                .font(.largeTitle.weight(.semibold))
                .foregroundStyle(palette.textPrimary)
            Text("Crée, organise et synchronise tes playlists en quelques clics.")
                .font(.body)
                .foregroundStyle(palette.textSecondary)
        }
    }

    @ViewBuilder
    private func attentionCard(palette: ThemePalette) -> some View {
        ProductSectionCard(title: "À traiter", palette: palette) {
            VStack(alignment: .leading, spacing: 8) {
                ForEach(workflow.libraryStore.playlistsNeedingAttention) { playlist in
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(playlist.name)
                                .font(.callout.weight(.semibold))
                            Text(PlaylistLibraryDisplay.syncStatusLabel(playlist.syncStatus))
                                .font(.caption)
                                .foregroundStyle(palette.textSecondary)
                        }
                        Spacer()
                        Button("Ouvrir") {
                            Task {
                                await workflow.libraryStore.select(localPlaylistID: playlist.localPlaylistID)
                                selection = .playlists
                            }
                        }
                        .buttonStyle(.bordered)
                    }
                }
                Button("Synchroniser maintenant") { selection = .sync }
                    .buttonStyle(.borderedProminent)
            }
        }
    }

    @ViewBuilder
    private func recentPlaylistsSection(palette: ThemePalette) -> some View {
        if workflow.libraryStore.recentPlaylists.isEmpty {
            ProductEmptyState(
                title: "Aucune playlist",
                message: "Crée ta première playlist ou importe-en une depuis un service musical.",
                systemImage: "music.note.list",
                palette: palette
            )
            Button("Créer une playlist") { selection = .newPlaylist }
                .buttonStyle(.borderedProminent)
        } else {
            VStack(alignment: .leading, spacing: 8) {
                ForEach(workflow.libraryStore.recentPlaylists) { playlist in
                    Button {
                        Task {
                            await workflow.libraryStore.select(localPlaylistID: playlist.localPlaylistID)
                            selection = .playlists
                        }
                    } label: {
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(playlist.name)
                                    .font(.callout.weight(.semibold))
                                Text("\(PlaylistLibraryDisplay.providerLabel(playlist.providerID)) · \(playlist.trackCount) morceaux")
                                    .font(.caption)
                                    .foregroundStyle(palette.textSecondary)
                            }
                            Spacer()
                            StatusChip(
                                label: PlaylistLibraryDisplay.syncStatusLabel(playlist.syncStatus),
                                color: syncStatusColor(playlist.syncStatus, palette: palette)
                            )
                        }
                    }
                    .buttonStyle(.plain)
                }
                Button("Voir toutes les playlists") { selection = .playlists }
                    .buttonStyle(.bordered)
            }
        }
    }

    @ViewBuilder
    private func quickActionsSection(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 120), spacing: 12)], spacing: 12) {
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

    private func syncStatusColor(_ status: PlaylistSyncStatus, palette: ThemePalette) -> Color {
        switch status {
        case .synced: return palette.statusSuccess
        case .conflict, .error: return palette.statusWarning
        case .pending, .partial: return palette.accentPrimary
        default: return palette.textSecondary
        }
    }
}
