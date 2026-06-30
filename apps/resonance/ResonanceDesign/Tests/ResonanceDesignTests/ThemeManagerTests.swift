import ResonanceDesign
import XCTest

@MainActor
final class ThemeManagerTests: XCTestCase {
    func testApplyNotifiesObserver() throws {
        let registry = try ThemeRegistry.loadBundled()
        let manager = try ThemeManager(registry: registry)
        let observer = ThemeObserver { _ in }
        var seen: [String] = []
        let tracked = ThemeObserver { theme in
            seen.append(theme.id)
        }

        manager.subscribe(tracked)
        try manager.apply(themeID: "apple_music_dark")
        XCTAssertEqual(seen, ["apple_music_dark"])

        manager.unsubscribe(tracked)
        try manager.apply(themeID: "classic_winamp_inspired")
        XCTAssertEqual(seen, ["apple_music_dark"])
        _ = observer
    }

    func testDefaultThemeIsAppleMusicLight() throws {
        let manager = try ThemeManager()
        XCTAssertEqual(manager.active.id, ThemeManager.defaultThemeID)
    }
}
