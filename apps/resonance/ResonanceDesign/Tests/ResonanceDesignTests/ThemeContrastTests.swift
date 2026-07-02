import ResonanceDesign
import XCTest

final class ThemeContrastTests: XCTestCase {
    func testBundledThemesHaveReadableContrast() throws {
        let registry = try ThemeRegistry.loadBundled()
        for theme in registry.list() {
            let colors = theme.tokens.colors
            let background = colors["color.background.primary"]!
            let surface = colors["color.surface"] ?? colors["color.background.secondary"]!
            let textPrimary = colors["color.text.primary"]!
            let inputBackground = colors["color.input.background"] ?? colors["color.background.elevated"]!
            let inputText = colors["color.input.text"] ?? colors["color.text.primary"]!
            let warning = colors["color.status.warning"]!
            let error = colors["color.status.error"]!

            XCTAssertTrue(
                ThemeContrast.hasReadableContrast(foregroundHex: textPrimary, backgroundHex: background),
                "\(theme.id): textPrimary vs background"
            )
            XCTAssertTrue(
                ThemeContrast.hasReadableContrast(foregroundHex: textPrimary, backgroundHex: surface),
                "\(theme.id): textPrimary vs surface"
            )
            XCTAssertTrue(
                ThemeContrast.hasReadableContrast(foregroundHex: inputText, backgroundHex: inputBackground),
                "\(theme.id): inputText vs inputBackground"
            )
            XCTAssertTrue(
                ThemeContrast.hasReadableContrast(foregroundHex: warning, backgroundHex: background),
                "\(theme.id): warning vs background"
            )
            XCTAssertTrue(
                ThemeContrast.hasReadableContrast(foregroundHex: error, backgroundHex: background),
                "\(theme.id): error vs background"
            )
        }
    }
}
