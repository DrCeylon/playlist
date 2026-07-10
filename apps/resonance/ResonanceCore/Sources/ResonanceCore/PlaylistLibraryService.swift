import Foundation

public protocol PlaylistLibraryServing: Sendable {
    func listManagedPlaylists() async throws -> [ManagedPlaylistSummary]
    func getManagedPlaylist(localPlaylistID: String) async throws -> ManagedPlaylistDetail?
    func importRemotePlaylist(remotePlaylist: RemotePlaylistSnapshot, origin: PlaylistOrigin) async throws -> ManagedPlaylistDetail?
    func syncManagedPlaylist(_ request: PlaylistSyncRequest) async throws -> PlaylistSyncResult
    func planSync(_ request: PlaylistSyncPlanRequest) async throws -> PlaylistSyncPlan?
    func applySync(_ request: PlaylistSyncApplyRequest) async throws -> PlaylistSyncApplyResult?
    func listRemotePlaylists(providerID: ProviderID) async throws -> [RemotePlaylist]
    func getRemotePlaylist(providerID: ProviderID, remotePlaylistID: String) async throws -> RemotePlaylistSnapshot?
}

public enum DefaultManagedPlaylists {
    public static let samples: [ManagedPlaylistSummary] = [
        ManagedPlaylistSummary(
            localPlaylistID: "sample-apple-1",
            name: "Soirée Chill",
            providerID: .appleMusic,
            trackCount: 24,
            syncStatus: .synced,
            lastSyncedAtISO: "2026-07-08T18:30:00",
            providerPlaylistID: "p.apple.demo.1",
            sourceKind: .generatedImport,
            importStatus: .imported,
            historySessionID: "hist-sample-1"
        ),
        ManagedPlaylistSummary(
            localPlaylistID: "sample-youtube-1",
            name: "Découvertes YouTube",
            providerID: .youtubeMusic,
            trackCount: 18,
            syncStatus: .pending,
            lastSyncedAtISO: "",
            providerPlaylistID: "",
            sourceKind: .providerLibrary,
            importStatus: .partialSuccess,
            historySessionID: "hist-sample-2"
        ),
    ]
}
