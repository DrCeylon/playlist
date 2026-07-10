import ResonanceCore
@testable import ResonanceMac
import XCTest

final class HomeNavigationTests: XCTestCase {
    func testHomeShortcutsTargetSidebarDestinations() {
        XCTAssertEqual(HomeShortcut.newPlaylist.destination, .newPlaylist)
        XCTAssertEqual(HomeShortcut.playlists.destination, .playlists)
        XCTAssertEqual(HomeShortcut.sync.destination, .sync)
        XCTAssertEqual(HomeShortcut.providers.destination, .providers)
        XCTAssertEqual(HomeShortcut.history.destination, .history)
    }

    func testHomeShortcutTitlesAreHumanReadable() {
        XCTAssertEqual(HomeShortcut.newPlaylist.title, "Créer une playlist")
        XCTAssertEqual(HomeShortcut.providers.title, SidebarItem.providers.title)
    }

    func testWorkflowShortcutsAreMarked() {
        XCTAssertTrue(HomeShortcut.newPlaylist.triggersWorkflow)
        XCTAssertTrue(HomeShortcut.history.triggersWorkflow)
        XCTAssertFalse(HomeShortcut.playlists.triggersWorkflow)
        XCTAssertFalse(HomeShortcut.sync.triggersWorkflow)
        XCTAssertFalse(HomeShortcut.providers.triggersWorkflow)
    }

    func testSidebarExcludesLaboratory() {
        XCTAssertFalse(SidebarItem.allCases.contains(where: { $0.title == "Laboratoire" }))
    }
}
