import ResonanceCore
@testable import ResonanceMac
import XCTest

final class HomeNavigationTests: XCTestCase {
    func testHomeShortcutsTargetSidebarDestinations() {
        XCTAssertEqual(HomeShortcut.newPlaylist.destination, .newPlaylist)
        XCTAssertEqual(HomeShortcut.playlists.destination, .playlists)
        XCTAssertEqual(HomeShortcut.sync.destination, .sync)
        XCTAssertEqual(HomeShortcut.history.destination, .history)
        XCTAssertEqual(HomeShortcut.laboratory.destination, .laboratory)
    }

    func testHomeShortcutTitlesMatchSidebarLabels() {
        XCTAssertEqual(HomeShortcut.newPlaylist.title, SidebarItem.newPlaylist.title)
        XCTAssertEqual(HomeShortcut.playlists.title, SidebarItem.playlists.title)
        XCTAssertEqual(HomeShortcut.sync.title, SidebarItem.sync.title)
        XCTAssertEqual(HomeShortcut.history.title, SidebarItem.history.title)
        XCTAssertEqual(HomeShortcut.laboratory.title, SidebarItem.laboratory.title)
    }

    func testWorkflowShortcutsAreMarked() {
        XCTAssertTrue(HomeShortcut.newPlaylist.triggersWorkflow)
        XCTAssertTrue(HomeShortcut.history.triggersWorkflow)
        XCTAssertFalse(HomeShortcut.playlists.triggersWorkflow)
        XCTAssertFalse(HomeShortcut.sync.triggersWorkflow)
        XCTAssertFalse(HomeShortcut.laboratory.triggersWorkflow)
    }
}
