import ResonanceDesign
import SwiftUI
import XCTest

@MainActor
final class ThemeManagerTests: XCTestCase {
    func testApplyNotifiesObserver() throws {
        let registry = try ThemeRegistry.loadBundled()
        let manager = try ThemeManager(registry: registry)
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
    }

    func testDefaultThemeIsSystem() throws {
        let defaults = UserDefaults.standard
        let key = "resonance.selectedThemeID"
        let previous = defaults.string(forKey: key)
        defer {
            if let previous {
                defaults.set(previous, forKey: key)
            } else {
                defaults.removeObject(forKey: key)
            }
        }
        defaults.removeObject(forKey: key)

        let manager = try ThemeManager()
        XCTAssertEqual(manager.selectedThemeID, ThemeManager.systemThemeID)
        XCTAssertEqual(manager.active.id, "apple_music_light")
    }

    func testSystemThemeSwitchesActiveTokensWithColorScheme() throws {
        let registry = try ThemeRegistry.loadBundled()
        let manager = try ThemeManager(registry: registry, defaultThemeID: ThemeManager.systemThemeID)
        try manager.apply(themeID: ThemeManager.systemThemeID)

        manager.updateColorScheme(.light)
        XCTAssertEqual(manager.active.id, "apple_music_light")

        manager.updateColorScheme(.dark)
        XCTAssertEqual(manager.active.id, "apple_music_dark")
    }

    func testManualThemeIgnoresSystemColorSchemeChanges() throws {
        let registry = try ThemeRegistry.loadBundled()
        let manager = try ThemeManager(registry: registry)
        try manager.apply(themeID: "classic_winamp_inspired")

        manager.updateColorScheme(.light)
        XCTAssertEqual(manager.active.id, "classic_winamp_inspired")

        manager.updateColorScheme(.dark)
        XCTAssertEqual(manager.active.id, "classic_winamp_inspired")
    }

    func testThemeOptionsIncludeSystemFirst() throws {
        let manager = try ThemeManager()
        XCTAssertEqual(manager.themeOptions.first?.themeID, ThemeManager.systemThemeID)
        XCTAssertEqual(manager.themeOptions.first?.displayName, "Système")
        XCTAssertEqual(manager.themeOptions.count, 4)
    }

    func testActiveDisplayNameReflectsSystemSelection() throws {
        let registry = try ThemeRegistry.loadBundled()
        let manager = try ThemeManager(registry: registry, defaultThemeID: ThemeManager.systemThemeID)
        try manager.apply(themeID: ThemeManager.systemThemeID)

        manager.updateColorScheme(.light)
        XCTAssertTrue(manager.activeDisplayName.hasPrefix("Système ("))
        XCTAssertTrue(manager.activeDisplayName.contains("Apple Music Light"))
    }
}
