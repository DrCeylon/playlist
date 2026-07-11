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
}
