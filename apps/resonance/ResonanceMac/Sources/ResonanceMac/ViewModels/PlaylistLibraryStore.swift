import Foundation
import ResonanceCore

@MainActor
final class PlaylistLibraryStore: ObservableObject {
    @Published private(set) var playlists: [ManagedPlaylistSummary] = []
    @Published private(set) var selectedDetail: ManagedPlaylistDetail?
    @Published private(set) var isBusy = false
    @Published var actionFeedback: String?

    private let service: any PlaylistLibraryServing

    init(service: any PlaylistLibraryServing) {
        self.service = service
    }

    var recentPlaylists: [ManagedPlaylistSummary] {
        Array(playlists.prefix(5))
    }

    var playlistsNeedingAttention: [ManagedPlaylistSummary] {
        playlists.filter { $0.syncStatus == .conflict || $0.syncStatus == .error || $0.syncStatus == .pending }
    }

    func refresh() async {
        isBusy = true
        defer { isBusy = false }
        do {
            playlists = try await service.listManagedPlaylists()
            actionFeedback = nil
        } catch {
            actionFeedback = "Impossible de charger vos playlists."
        }
    }

    func select(localPlaylistID: String) async {
        isBusy = true
        defer { isBusy = false }
        do {
            selectedDetail = try await service.getManagedPlaylist(localPlaylistID: localPlaylistID)
        } catch {
            actionFeedback = "Impossible d'afficher cette playlist."
        }
    }

    func clearSelection() {
        selectedDetail = nil
    }
}
