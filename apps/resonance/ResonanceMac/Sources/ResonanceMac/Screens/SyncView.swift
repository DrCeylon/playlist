import ResonanceCore
import ResonanceDesign
import SwiftUI

struct SyncView: View {
    @StateObject private var viewModel: PlaylistsViewModel
    @Binding var selection: SidebarItem?
    @EnvironmentObject private var themeManager: ThemeManager

    init(
        selection: Binding<SidebarItem?>,
        libraryService: any PlaylistLibraryServing = MockPlaylistLibraryService()
    ) {
        _selection = selection
        _viewModel = StateObject(wrappedValue: PlaylistsViewModel(service: libraryService))
    }

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header(palette: palette)
                    if let feedback = viewModel.actionFeedback {
                        Text(feedback)
                            .font(.callout)
                            .foregroundStyle(palette.textSecondary)
                    }
                    syncCandidates(palette: palette)
                    assumptionsCard(palette: palette)
                }
                .padding(24)
            }
        }
        .navigationTitle("Synchronisation")
        .task { await viewModel.refresh() }
    }

    @ViewBuilder
    private func header(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Synchroniser les playlists")
                .font(.title2.weight(.semibold))
                .foregroundStyle(palette.textPrimary)
            Text("Récupère une copie locale manipulable depuis un provider personnel ou une playlist publique, puis prépare une version personnalisée.")
                .font(.callout)
                .foregroundStyle(palette.textSecondary)
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }

    @ViewBuilder
    private func syncCandidates(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Playlists à synchroniser")
                .font(.headline)
            if viewModel.playlists.isEmpty {
                Text("Aucune playlist locale — commence par générer ou importer une playlist.")
                    .font(.callout)
                    .foregroundStyle(palette.textSecondary)
            } else {
                ForEach(viewModel.playlists) { playlist in
                    HStack(alignment: .top) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(playlist.name)
                                .font(.callout.weight(.semibold))
                            Text("\(PlaylistLibraryDisplay.providerLabel(playlist.providerID)) · \(PlaylistLibraryDisplay.syncStatusLabel(playlist.syncStatus))")
                                .font(.caption)
                                .foregroundStyle(palette.textSecondary)
                        }
                        Spacer()
                        Button("Sync") {
                            Task {
                                await viewModel.select(localPlaylistID: playlist.localPlaylistID)
                                await viewModel.syncSelected(direction: .pullFromProvider)
                            }
                        }
                        .buttonStyle(.bordered)
                        .disabled(viewModel.isBusy)
                    }
                    .padding(.vertical, 4)
                }
            }
            Button("Ouvrir le gestionnaire de playlists") {
                selection = .playlists
            }
            .buttonStyle(.borderedProminent)
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }

    @ViewBuilder
    private func assumptionsCard(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Limites actuelles")
                .font(.headline)
            Text("• Apple Music reste le provider principal pour l'import livré.")
            Text("• YouTube Music est expérimental : contrats bridge prêts, gateway réel à valider.")
            Text("• Les conflits (suppression locale, ajout provider, metadata) sont modélisés mais la résolution automatique arrive dans une phase ultérieure.")
        }
        .font(.caption)
        .foregroundStyle(palette.textSecondary)
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }
}
