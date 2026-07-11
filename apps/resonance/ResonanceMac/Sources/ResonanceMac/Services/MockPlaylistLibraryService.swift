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

    public func planSync(_ request: PlaylistSyncPlanRequest) async throws -> PlaylistSyncPlanResult? {
        nil
    }

    public func resolveSyncConflicts(_ request: PlaylistSyncResolveRequest) async throws -> PlaylistSyncPlanResult? {
        nil
    }

    public func applySync(_ request: PlaylistSyncApplyRequest) async throws -> PlaylistSyncApplyResult? {
        nil
    }

    public func listRemotePlaylists(providerID: ProviderID) async throws -> [RemotePlaylist] {
        []
    }

    public func getRemotePlaylist(providerID: ProviderID, remotePlaylistID: String) async throws -> RemotePlaylistSnapshot? {
        nil
    }

    public func importRemotePlaylist(
        remotePlaylist: RemotePlaylistSnapshot,
        origin: PlaylistOrigin
    ) async throws -> ManagedPlaylistDetail? {
        guard let summary = playlists.first else { return nil }
        return ManagedPlaylistDetail(summary: summary, tracks: [])
    }
}
