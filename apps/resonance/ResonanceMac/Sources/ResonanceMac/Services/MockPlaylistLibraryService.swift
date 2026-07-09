import Foundation
import ResonanceCore

public struct MockPlaylistLibraryService: PlaylistLibraryServing {
    public var playlists: [ManagedPlaylistSummary]
    public var detailsByID: [String: ManagedPlaylistDetail]

    public init(
        playlists: [ManagedPlaylistSummary] = DefaultManagedPlaylists.samples,
        detailsByID: [String: ManagedPlaylistDetail] = [:]
    ) {
        self.playlists = playlists
        self.detailsByID = detailsByID
    }

    public func listManagedPlaylists() async throws -> [ManagedPlaylistSummary] {
        playlists
    }

    public func getManagedPlaylist(localPlaylistID: String) async throws -> ManagedPlaylistDetail? {
        if let detail = detailsByID[localPlaylistID] {
            return detail
        }
        guard let summary = playlists.first(where: { $0.localPlaylistID == localPlaylistID }) else {
            return nil
        }
        return ManagedPlaylistDetail(summary: summary, tracks: [])
    }

    public func syncManagedPlaylist(_ request: PlaylistSyncRequest) async throws -> PlaylistSyncResult {
        PlaylistSyncResult(
            localPlaylistID: request.localPlaylistID,
            syncStatus: .pending,
            message: "Synchronisation simulée — gateway provider en cours d'intégration."
        )
    }

    public func planSync(_ request: PlaylistSyncPlanRequest) async throws -> PlaylistSyncPlan? {
        nil
    }
}
