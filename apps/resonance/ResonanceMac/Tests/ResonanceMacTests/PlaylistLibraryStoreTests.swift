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
}
