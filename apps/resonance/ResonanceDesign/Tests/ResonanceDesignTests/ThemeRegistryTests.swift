import ResonanceDesign
import XCTest

final class ThemeRegistryTests: XCTestCase {
    func testLoadBundledThemes() throws {
        let registry = try ThemeRegistry.loadBundled()
        let ids = Set(registry.list().map(\.id))
        XCTAssertEqual(ids, ["apple_music_dark", "apple_music_light", "classic_winamp_inspired"])
    }

    func testBundledThemesValidate() throws {
        let registry = try ThemeRegistry.loadBundled()
        for theme in registry.list() {
            XCTAssertNoThrow(try ThemeValidation.validate(theme: theme))
        }
    }

    func testInheritanceMerge() throws {
        let registry = try ThemeRegistry.loadBundled()
        let parent = try registry.get("apple_music_dark")
        let child = try registry.get("classic_winamp_inspired")

        XCTAssertEqual(child.extends, "apple_music_dark")
        XCTAssertEqual(child.tokens.colors["color.background.primary"], "#232323")
        XCTAssertEqual(child.tokens.colors["color.text.primary"], parent.tokens.colors["color.text.primary"])
        XCTAssertEqual(child.tokens.colors["color.accent.primary"], "#00FF99")
    }

    func testUnknownThemeThrows() throws {
        let registry = try ThemeRegistry.loadBundled()
        XCTAssertThrowsError(try registry.get("missing")) { error in
            XCTAssertEqual(error as? ThemeError, .notFound("missing"))
        }
    }
}
