import ResonanceCore
import ResonanceDesign
import SwiftUI

struct PlaylistsView: View {
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
            HStack(alignment: .top, spacing: 16) {
                playlistList(palette: palette)
                    .frame(minWidth: 280, maxWidth: 360)
                playlistDetail(palette: palette)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            }
            .padding(24)
        }
        .navigationTitle("Playlists")
        .task { await viewModel.refresh() }
    }

    @ViewBuilder
    private func playlistList(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Playlists locales")
                .font(.title3.weight(.semibold))
                .foregroundStyle(palette.textPrimary)
            if let feedback = viewModel.actionFeedback {
                Text(feedback)
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
            }
            if viewModel.isBusy && viewModel.playlists.isEmpty {
                ProgressView()
            } else if viewModel.playlists.isEmpty {
                Text("Aucune playlist enregistrée pour le moment.")
                    .font(.callout)
                    .foregroundStyle(palette.textSecondary)
            } else {
                List(viewModel.playlists) { playlist in
                    Button {
                        Task { await viewModel.select(localPlaylistID: playlist.localPlaylistID) }
                    } label: {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(playlist.name)
                                .font(.headline)
                            Text("\(PlaylistLibraryDisplay.providerLabel(playlist.providerID)) · \(playlist.trackCount) morceaux")
                                .font(.caption)
                                .foregroundStyle(palette.textSecondary)
                            Text(PlaylistLibraryDisplay.syncStatusLabel(playlist.syncStatus))
                                .font(.caption2)
                                .foregroundStyle(palette.accentPrimary)
                        }
                    }
                    .buttonStyle(.plain)
                }
                .listStyle(.sidebar)
            }
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }

    @ViewBuilder
    private func playlistDetail(palette: ThemePalette) -> some View {
        if let detail = viewModel.selectedDetail {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text(detail.summary.name)
                        .font(.title2.weight(.semibold))
                        .foregroundStyle(palette.textPrimary)
                    detailMetrics(detail.summary, palette: palette)
                    actionRow(detail.summary, palette: palette)
                    if !detail.syncConflicts.isEmpty {
                        conflictsSection(detail.syncConflicts, palette: palette)
                    }
                    tracksSection(detail.tracks, palette: palette)
                }
            }
            .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
        } else {
            VStack(alignment: .leading, spacing: 8) {
                Text("Sélectionne une playlist")
                    .font(.title3.weight(.semibold))
                    .foregroundStyle(palette.textPrimary)
                Text("Consulte le statut d'import, la synchronisation provider et les morceaux connus localement.")
                    .font(.callout)
                    .foregroundStyle(palette.textSecondary)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
        }
    }

    @ViewBuilder
    private func detailMetrics(_ summary: ManagedPlaylistSummary, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            metricRow("Provider", PlaylistLibraryDisplay.providerLabel(summary.providerID), palette: palette)
            metricRow("Synchronisation", PlaylistLibraryDisplay.syncStatusLabel(summary.syncStatus), palette: palette)
            if let importStatus = summary.importStatus {
                metricRow("Import", SessionHistoryDisplay.statusLabel(for: importStatus), palette: palette)
            }
            if !summary.lastSyncedAtISO.isEmpty {
                metricRow("Dernière sync", summary.lastSyncedAtISO, palette: palette)
            }
        }
    }

    @ViewBuilder
    private func actionRow(_ summary: ManagedPlaylistSummary, palette: ThemePalette) -> some View {
        HStack(spacing: 12) {
            Button("Synchroniser") {
                Task { await viewModel.syncSelected(direction: .pullFromProvider) }
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isBusy)
            Button("Réessayer les introuvables") {
                selection = .history
            }
            .buttonStyle(.bordered)
            Button("Historique") {
                selection = .history
            }
            .buttonStyle(.bordered)
        }
        .font(.callout)
    }

    @ViewBuilder
    private func conflictsSection(_ conflicts: [PlaylistSyncConflict], palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Conflits")
                .font(.headline)
            ForEach(conflicts) { conflict in
                Text("• \(conflict.message)")
                    .font(.caption)
                    .foregroundStyle(palette.statusWarning)
            }
        }
    }

    @ViewBuilder
    private func tracksSection(_ tracks: [ManagedPlaylistTrack], palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Morceaux")
                .font(.headline)
            if tracks.isEmpty {
                Text("Aucun morceau détaillé pour cette playlist — structure prête pour l'édition future.")
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
            } else {
                ForEach(tracks) { track in
                    HStack {
                        VStack(alignment: .leading) {
                            Text(track.title).font(.callout.weight(.medium))
                            Text(track.artist).font(.caption).foregroundStyle(palette.textSecondary)
                        }
                        Spacer()
                        Text(track.mappingStatus.rawValue)
                            .font(.caption2)
                            .foregroundStyle(palette.textSecondary)
                    }
                }
            }
        }
    }

    private func metricRow(_ title: String, _ value: String, palette: ThemePalette) -> some View {
        HStack {
            Text(title).foregroundStyle(palette.textSecondary)
            Spacer()
            Text(value).foregroundStyle(palette.textPrimary)
        }
        .font(.callout)
    }
}
