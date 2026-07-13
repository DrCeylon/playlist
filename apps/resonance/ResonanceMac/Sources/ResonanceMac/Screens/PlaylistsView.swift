import ResonanceCore
import ResonanceDesign
import SwiftUI

struct PlaylistsView: View {
    @Binding var selection: SidebarItem?
    @ObservedObject var libraryStore: PlaylistLibraryStore
    @EnvironmentObject private var themeManager: ThemeManager
    @EnvironmentObject private var workflow: AppWorkflowCoordinator
    @State private var selectedPlaylistID: String?
    @State private var showRemoteImport = false

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
        .onAppear {
            syncListSelectionFromStore()
        }
        .onChange(of: libraryStore.selectedDetail?.summary.localPlaylistID) { _, _ in
            syncListSelectionFromStore()
        }
        .onChange(of: selectedPlaylistID) { _, playlistID in
            guard let playlistID else {
                if libraryStore.selectedDetail != nil {
                    libraryStore.clearSelection()
                }
                return
            }
            if libraryStore.selectedDetail?.summary.localPlaylistID == playlistID {
                return
            }
            Task { await libraryStore.select(localPlaylistID: playlistID) }
        }
        .refreshable { await libraryStore.refresh() }
        .sheet(isPresented: $showRemoteImport) {
            RemoteImportView(
                viewModel: RemoteImportViewModel(libraryService: workflow.engineBridge)
            )
            .frame(minWidth: 520, minHeight: 480)
        }
    }

    @ViewBuilder
    private func playlistList(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Mes playlists")
                .font(.title3.weight(.semibold))
                .foregroundStyle(palette.textPrimary)
            Button("Importer depuis un service") {
                showRemoteImport = true
            }
            .buttonStyle(.bordered)
            if let feedback = libraryStore.actionFeedback {
                Text(feedback)
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
            }
            if libraryStore.isBusy && libraryStore.playlists.isEmpty {
                ProgressView()
            } else if libraryStore.playlists.isEmpty {
                ProductEmptyState(
                    title: "Aucune playlist",
                    message: "Crée ou importe une playlist pour commencer.",
                    systemImage: "music.note.list",
                    palette: palette
                )
            } else {
                List(libraryStore.playlists, selection: $selectedPlaylistID) { playlist in
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(playlist.name)
                                .font(.headline)
                            Text("\(PlaylistLibraryDisplay.providerLabel(playlist.providerID)) · \(playlist.trackCount) morceaux")
                                .font(.caption)
                                .foregroundStyle(palette.textSecondary)
                        }
                        Spacer()
                        StatusChip(
                            label: PlaylistLibraryDisplay.syncStatusLabel(playlist.syncStatus),
                            color: palette.accentPrimary
                        )
                    }
                    .tag(playlist.localPlaylistID)
                }
                .listStyle(.sidebar)
            }
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }

    @ViewBuilder
    private func playlistDetail(palette: ThemePalette) -> some View {
        if let detail = libraryStore.selectedDetail {
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
            ProductEmptyState(
                title: "Sélectionne une playlist",
                message: "Consulte les morceaux, l'état de synchronisation et les différences à résoudre.",
                systemImage: "sidebar.left",
                palette: palette
            )
            .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
        }
    }

    @ViewBuilder
    private func detailMetrics(_ summary: ManagedPlaylistSummary, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            ProductMetricRow(title: "Service", value: PlaylistLibraryDisplay.providerLabel(summary.providerID), palette: palette)
            ProductMetricRow(title: "Synchronisation", value: PlaylistLibraryDisplay.syncStatusLabel(summary.syncStatus), palette: palette)
            if let importStatus = summary.importStatus {
                ProductMetricRow(title: "Import", value: SessionHistoryDisplay.statusLabel(for: importStatus), palette: palette)
            }
            if !summary.lastSyncedAtISO.isEmpty {
                ProductMetricRow(title: "Dernière sync", value: summary.lastSyncedAtISO, palette: palette)
            }
            ProductMetricRow(title: "Morceaux", value: "\(summary.trackCount)", palette: palette)
        }
    }

    @ViewBuilder
    private func actionRow(_ summary: ManagedPlaylistSummary, palette: ThemePalette) -> some View {
        HStack(spacing: 12) {
            Button("Synchroniser") {
                Task {
                    await libraryStore.select(localPlaylistID: summary.localPlaylistID)
                    selection = .sync
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(libraryStore.isBusy)
            Button("Historique") { selection = .history }
                .buttonStyle(.bordered)
        }
        .font(.callout)
    }

    @ViewBuilder
    private func conflictsSection(_ conflicts: [PlaylistSyncConflict], palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Différences à résoudre")
                .font(.headline)
            ForEach(conflicts) { conflict in
                HStack(alignment: .top, spacing: 8) {
                    StatusChip(
                        label: ProductDisplay.conflictSeverityLabel(conflict.severity),
                        color: palette.statusWarning
                    )
                    VStack(alignment: .leading, spacing: 2) {
                        Text(ProductDisplay.conflictKindLabel(conflict.conflictKind))
                            .font(.callout.weight(.medium))
                        Text(conflict.message)
                            .font(.caption)
                            .foregroundStyle(palette.textSecondary)
                    }
                }
            }
            Button("Résoudre les différences") {
                selection = .sync
            }
            .buttonStyle(.bordered)
        }
    }

    @ViewBuilder
    private func tracksSection(_ tracks: [ManagedPlaylistTrack], palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Morceaux")
                .font(.headline)
            if tracks.isEmpty {
                Text("Aucun morceau enregistré pour cette playlist.")
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
                        Text(ProductDisplay.mappingStatusLabel(track.mappingStatus))
                            .font(.caption2)
                            .foregroundStyle(palette.textSecondary)
                    }
                }
            }
        }
    }

    private func syncListSelectionFromStore() {
        let detailID = libraryStore.selectedDetail?.summary.localPlaylistID
        if selectedPlaylistID != detailID {
            selectedPlaylistID = detailID
        }
    }
}
