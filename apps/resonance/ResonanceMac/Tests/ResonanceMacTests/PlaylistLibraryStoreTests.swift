import Combine
import ResonanceCore
@testable import ResonanceMac
import XCTest

@MainActor
final class PlaylistLibraryStoreTests: XCTestCase {
    func testRecentPlaylistsReturnsFirstFive() async {
        let playlists = (1...8).map { index in
            ManagedPlaylistSummary(
                localPlaylistID: "id-\(index)",
                name: "Playlist \(index)",
                providerID: .appleMusic,
                trackCount: index,
                syncStatus: .synced
            )
        }
        let service = MockPlaylistLibraryService(playlists: playlists)
        let store = PlaylistLibraryStore(service: service)
        await store.refresh()
        XCTAssertEqual(store.recentPlaylists.count, 5)
        XCTAssertEqual(store.recentPlaylists.first?.name, "Playlist 1")
    }

    func testPlaylistsNeedingAttentionFiltersStatuses() async {
        let playlists = [
            ManagedPlaylistSummary(localPlaylistID: "1", name: "OK", providerID: .appleMusic, trackCount: 1, syncStatus: .synced),
            ManagedPlaylistSummary(localPlaylistID: "2", name: "Conflict", providerID: .appleMusic, trackCount: 1, syncStatus: .conflict),
        ]
        let store = PlaylistLibraryStore(service: MockPlaylistLibraryService(playlists: playlists))
        await store.refresh()
        XCTAssertEqual(store.playlistsNeedingAttention.count, 1)
        XCTAssertEqual(store.playlistsNeedingAttention.first?.name, "Conflict")
    }

    func testSelectDuringRefreshSetsSelectedDetail() async throws {
        let summary = ManagedPlaylistSummary(
            localPlaylistID: "playlist-first-open",
            name: "First Open",
            providerID: .appleMusic,
            trackCount: 3,
            syncStatus: .synced
        )
        let service = DelayedPlaylistLibraryService(
            playlists: [summary],
            listDelayNanoseconds: 200_000_000
        )
        let store = PlaylistLibraryStore(service: service)

        async let refreshTask: Void = store.refresh()
        await Task.yield()
        await store.select(localPlaylistID: summary.localPlaylistID)
        await refreshTask

        XCTAssertEqual(store.selectedDetail?.summary.localPlaylistID, summary.localPlaylistID)
        XCTAssertEqual(store.playlists.count, 1)
    }

    func testRepeatedRefreshPreservesSelection() async {
        let summary = ManagedPlaylistSummary(
            localPlaylistID: "playlist-refresh-cycle",
            name: "Refresh Cycle",
            providerID: .appleMusic,
            trackCount: 2,
            syncStatus: .synced
        )
        let service = MockPlaylistLibraryService(playlists: [summary])
        let store = PlaylistLibraryStore(service: service)

        await store.refresh()
        await store.select(localPlaylistID: summary.localPlaylistID)
        await store.refresh()
        await store.refresh()

        XCTAssertEqual(store.selectedDetail?.summary.localPlaylistID, summary.localPlaylistID)
        XCTAssertFalse(store.isBusy)
    }

    func testConcurrentRefreshAndSelectKeepsBusyUntilBothFinish() async throws {
        let summary = ManagedPlaylistSummary(
            localPlaylistID: "playlist-busy",
            name: "Busy Tracking",
            providerID: .appleMusic,
            trackCount: 1,
            syncStatus: .synced
        )
        let service = DelayedPlaylistLibraryService(
            playlists: [summary],
            listDelayNanoseconds: 100_000_000,
            detailDelayNanoseconds: 100_000_000
        )
        let store = PlaylistLibraryStore(service: service)

        async let refreshTask: Void = store.refresh()
        await Task.yield()
        async let selectTask: Void = store.select(localPlaylistID: summary.localPlaylistID)
        XCTAssertTrue(store.isBusy)
        await refreshTask
        XCTAssertTrue(store.isBusy)
        await selectTask
        XCTAssertFalse(store.isBusy)
    }
}

@MainActor
private final class DelayedPlaylistLibraryService: PlaylistLibraryServing, @unchecked Sendable {
    let playlists: [ManagedPlaylistSummary]
    let listDelayNanoseconds: UInt64
    let detailDelayNanoseconds: UInt64

    init(
        playlists: [ManagedPlaylistSummary],
        listDelayNanoseconds: UInt64 = 0,
        detailDelayNanoseconds: UInt64 = 0
    ) {
        self.playlists = playlists
        self.listDelayNanoseconds = listDelayNanoseconds
        self.detailDelayNanoseconds = detailDelayNanoseconds
    }

    func listManagedPlaylists() async throws -> [ManagedPlaylistSummary] {
        if listDelayNanoseconds > 0 {
            try await Task.sleep(nanoseconds: listDelayNanoseconds)
        }
        return playlists
    }

    func getManagedPlaylist(localPlaylistID: String) async throws -> ManagedPlaylistDetail? {
        if detailDelayNanoseconds > 0 {
            try await Task.sleep(nanoseconds: detailDelayNanoseconds)
        }
        guard let summary = playlists.first(where: { $0.localPlaylistID == localPlaylistID }) else {
            return nil
        }
        return ManagedPlaylistDetail(summary: summary, tracks: [])
    }

    func planSync(_ request: PlaylistSyncPlanRequest) async throws -> PlaylistSyncPlanResult? { nil }
    func resolveSyncConflicts(_ request: PlaylistSyncResolveRequest) async throws -> PlaylistSyncPlanResult? { nil }
    func applySync(_ request: PlaylistSyncApplyRequest) async throws -> PlaylistSyncApplyResult? { nil }
    func listRemotePlaylists(providerID: ProviderID) async throws -> [RemotePlaylist] { [] }
    func getRemotePlaylist(providerID: ProviderID, remotePlaylistID: String) async throws -> RemotePlaylistSnapshot? { nil }
    func importRemotePlaylist(remotePlaylist: RemotePlaylistSnapshot, origin: PlaylistOrigin) async throws -> ManagedPlaylistDetail? { nil }
}
