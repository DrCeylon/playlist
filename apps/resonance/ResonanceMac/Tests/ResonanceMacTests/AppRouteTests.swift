import ResonanceCore
import XCTest

final class AppRouteTests: XCTestCase {
    func testSidebarRoutesMatchPythonContract() {
        XCTAssertEqual(SidebarItem.home.route.rawValue, "home")
        XCTAssertEqual(SidebarItem.newPlaylist.route.rawValue, "new_playlist")
        XCTAssertEqual(SidebarItem.playlists.route.rawValue, "playlists")
        XCTAssertEqual(SidebarItem.sync.route.rawValue, "sync")
        XCTAssertEqual(SidebarItem.providers.route.rawValue, "providers")
        XCTAssertEqual(SidebarItem.history.route.rawValue, "history")
        XCTAssertEqual(SidebarItem.laboratory.route.rawValue, "diagnostics")
        XCTAssertEqual(SidebarItem.settings.route.rawValue, "settings")
    }

    func testFrenchSidebarTitles() {
        XCTAssertEqual(SidebarItem.home.title, "Accueil")
        XCTAssertEqual(SidebarItem.newPlaylist.title, "Nouvelle Playlist")
        XCTAssertEqual(SidebarItem.playlists.title, "Playlists")
        XCTAssertEqual(SidebarItem.sync.title, "Synchronisation")
        XCTAssertEqual(SidebarItem.providers.title, "Providers")
        XCTAssertEqual(SidebarItem.history.title, "Historique")
        XCTAssertEqual(SidebarItem.laboratory.title, "Laboratoire")
        XCTAssertEqual(SidebarItem.settings.title, "Paramètres")
    }
}
