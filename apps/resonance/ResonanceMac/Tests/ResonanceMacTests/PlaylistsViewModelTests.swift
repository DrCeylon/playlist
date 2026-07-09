import ResonanceCore
@testable import ResonanceMac
import XCTest

@MainActor
final class PlaylistsViewModelTests: XCTestCase {
    func testRefreshLoadsManagedPlaylists() async {
        let service = MockPlaylistLibraryService(
            playlists: [
                ManagedPlaylistSummary(
                    localPlaylistID: "p1",
                    name: "Test",
                    providerID: .appleMusic,
                    trackCount: 3,
                    syncStatus: .synced
                ),
            ]
        )
        let viewModel = PlaylistsViewModel(service: service)
        await viewModel.refresh()
        XCTAssertEqual(viewModel.playlists.count, 1)
        XCTAssertEqual(viewModel.playlists[0].name, "Test")
    }

    func testSyncSelectedReturnsPendingMessage() async {
        let service = MockPlaylistLibraryService(
            playlists: [
                ManagedPlaylistSummary(
                    localPlaylistID: "p1",
                    name: "Test",
                    providerID: .youtubeMusic,
                    trackCount: 1,
                    syncStatus: .notLinked
                ),
            ]
        )
        let viewModel = PlaylistsViewModel(service: service)
        await viewModel.refresh()
        await viewModel.select(localPlaylistID: "p1")
        await viewModel.syncSelected(direction: .pullFromProvider)
        XCTAssertEqual(
            viewModel.actionFeedback,
            "Synchronisation simulée — gateway provider en cours d'intégration."
        )
    }
}
