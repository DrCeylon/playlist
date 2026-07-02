import XCTest

final class PlaylistBuilderFormGuardTests: XCTestCase {
    func testPlaylistBuilderUsesNativeEditableTextFields() throws {
        let source = try loadPlaylistBuilderSource()
        let keyboardFieldSource = try loadMacKeyboardTextFieldSource()

        XCTAssertTrue(
            source.contains("MacKeyboardTextField"),
            "Playlist builder must use AppKit-backed MacKeyboardTextField for reliable macOS typing"
        )
        XCTAssertFalse(source.contains("ThemedTextField"), "Custom ThemedTextField blocks macOS editing")
        XCTAssertTrue(
            source.contains("KeyboardInputDebugPanel"),
            "Temporary keyboard debug panel must be present for macOS validation"
        )
        XCTAssertTrue(
            source.contains("@State private var draftName"),
            "Form draft fields must use local @State for macOS TextField bindings"
        )
        XCTAssertTrue(
            source.contains("func pushDraftToViewModel()"),
            "Draft state must sync into the view model"
        )
        XCTAssertTrue(
            keyboardFieldSource.contains("NSTextField"),
            "Mac keyboard field must wrap NSTextField"
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

    private func loadMacKeyboardTextFieldSource() throws -> String {
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/ResonanceMac/Components/MacKeyboardTextField.swift")
        return try String(contentsOf: root, encoding: .utf8)
    }
}
