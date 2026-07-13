import ResonanceCore
@testable import ResonanceMac
import XCTest

@MainActor
final class SyncViewModelTests: XCTestCase {
    func testSelectPlaylistResetsState() {
        let model = SyncViewModel(service: MockPlaylistLibraryService())
        model.selectPlaylist("playlist-1")
        XCTAssertEqual(model.selectedPlaylistID, "playlist-1")
        model.reset()
        XCTAssertNil(model.selectedPlaylistID)
        XCTAssertEqual(model.step, .selectPlaylist)
    }

    func testUpdateResolutionStoresChoice() {
        let model = SyncViewModel(service: MockPlaylistLibraryService())
        model.updateResolution(conflictID: "conflict-1", strategy: "keep_local")
        XCTAssertEqual(model.resolutionChoices["conflict-1"], "keep_local")
    }

    func testPreviewPlanUsesLinkedRemotePlaylistID() async {
        let linkedRef = LinkedRemoteRef(
            providerID: .appleMusic,
            remotePlaylistID: "remote-linked-42",
            snapshotChecksum: "checksum-42"
        )
        let summary = ManagedPlaylistSummary(
            localPlaylistID: "hist-1",
            name: "Linked Playlist",
            providerID: .appleMusic,
            trackCount: 1,
            syncStatus: .synced,
            providerPlaylistID: "",
            linkedRemoteRefs: [linkedRef]
        )
        let detail = ManagedPlaylistDetail(
            summary: summary,
            tracks: [
                ManagedPlaylistTrack(
                    localTrackID: "tr-1",
                    artist: "Artist",
                    title: "Title",
                    mappingStatus: .matched
                ),
            ]
        )
        let service = CapturingPlanSyncService()
        let model = SyncViewModel(service: service)
        await model.previewPlan(for: detail)
        XCTAssertEqual(service.lastPlanRequest?.remotePlaylistID, "remote-linked-42")
    }
}

@MainActor
private final class CapturingPlanSyncService: PlaylistLibraryServing, @unchecked Sendable {
    private(set) var lastPlanRequest: PlaylistSyncPlanRequest?

    func listManagedPlaylists() async throws -> [ManagedPlaylistSummary] { [] }
    func getManagedPlaylist(localPlaylistID: String) async throws -> ManagedPlaylistDetail? { nil }

    func planSync(_ request: PlaylistSyncPlanRequest) async throws -> PlaylistSyncPlanResult? {
        lastPlanRequest = request
        return PlaylistSyncPlanResult(
            plan: PlaylistSyncPlan(
                localPlaylistID: request.localPlaylistID,
                targetProviderID: request.providerID,
                direction: request.direction,
                syncMode: request.syncMode,
                remotePlaylistID: request.remotePlaylistID,
                actions: [],
                conflicts: []
            ),
            planChecksum: "checksum"
        )
    }

    func resolveSyncConflicts(_ request: PlaylistSyncResolveRequest) async throws -> PlaylistSyncPlanResult? { nil }
    func applySync(_ request: PlaylistSyncApplyRequest) async throws -> PlaylistSyncApplyResult? { nil }
    func listRemotePlaylists(providerID: ProviderID) async throws -> [RemotePlaylist] { [] }
    func getRemotePlaylist(providerID: ProviderID, remotePlaylistID: String) async throws -> RemotePlaylistSnapshot? { nil }
    func importRemotePlaylist(remotePlaylist: RemotePlaylistSnapshot, origin: PlaylistOrigin) async throws -> ManagedPlaylistDetail? { nil }
}
