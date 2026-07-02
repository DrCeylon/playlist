import XCTest

final class PlaylistBuilderFormGuardTests: XCTestCase {
    func testPlaylistBuilderUsesAppKitBackedTextFields() throws {
        let source = try loadPlaylistBuilderSource()
        let appKitFieldSource = try loadAppKitTextFieldSource()

        XCTAssertTrue(
            source.contains("GenerateFooterSection"),
            "Generate button must live in a sticky footer outside the scroll view"
        )
        XCTAssertTrue(
            source.contains(".frame(maxWidth: .infinity, maxHeight: .infinity"),
            "Scroll view must receive a bounded height so macOS scrolling works"
        )
        XCTAssertTrue(
            source.contains("AppKitTextField"),
            "Playlist builder must use AppKit-backed text fields for macOS keyboard input"
        )
        XCTAssertTrue(
            source.contains("DebugInputSection") || source.contains("ResonanceFeatureFlags.keyboardDebugEnabled"),
            "Keyboard debug probe must be available behind dev flag"
        )
        XCTAssertFalse(source.contains("ThemedTextField"), "Custom ThemedTextField blocks macOS editing")
        XCTAssertFalse(source.contains("Form {"), "SwiftUI Form can steal macOS keyboard focus")
        XCTAssertTrue(
            source.contains("@State private var draftName"),
            "Form draft fields must use local @State for macOS TextField bindings"
        )
        XCTAssertTrue(
            source.contains("func pushDraftToViewModel()"),
            "Draft state must sync into the view model"
        )
        XCTAssertTrue(
            appKitFieldSource.contains("KeyableNSTextField"),
            "AppKit text field must use a keyable NSTextField subclass"
        )
    }

    private func loadPlaylistBuilderSource() throws -> String {
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/ResonanceMac/Screens/PlaylistBuilderView.swift")
        return try String(contentsOf: root, encoding: .utf8)
    }

    private func loadAppKitTextFieldSource() throws -> String {
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/ResonanceMac/Components/AppKitTextField.swift")
        return try String(contentsOf: root, encoding: .utf8)
    }
}
