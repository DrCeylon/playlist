import ResonanceCore
@testable import ResonanceMac
import XCTest

final class HomeNavigationTests: XCTestCase {
    func testHomeShortcutsTargetSidebarDestinations() {
        XCTAssertEqual(HomeShortcut.newPlaylist.destination, .newPlaylist)
        XCTAssertEqual(HomeShortcut.history.destination, .history)
        XCTAssertEqual(HomeShortcut.laboratory.destination, .laboratory)
    }

    func testHomeShortcutTitlesMatchSidebarLabels() {
        XCTAssertEqual(HomeShortcut.newPlaylist.title, SidebarItem.newPlaylist.title)
        XCTAssertEqual(HomeShortcut.history.title, SidebarItem.history.title)
        XCTAssertEqual(HomeShortcut.laboratory.title, SidebarItem.laboratory.title)
    }
}
