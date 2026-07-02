import XCTest

final class PlaylistBuilderFormGuardTests: XCTestCase {
    func testPlaylistBuilderUsesNativeEditableTextFields() throws {
        let source = try loadPlaylistBuilderSource()

        XCTAssertTrue(source.contains("TextField("), "Playlist builder must use SwiftUI TextField")
        XCTAssertFalse(source.contains("ThemedTextField"), "Custom ThemedTextField blocks macOS editing")
        XCTAssertTrue(
            source.contains(".textFieldStyle(.roundedBorder)"),
            "macOS requires roundedBorder text fields for reliable editing"
        )
        XCTAssertTrue(
            source.contains("@State private var draftName"),
            "Form draft fields must use local @State for macOS TextField bindings"
        )
        XCTAssertTrue(
            source.contains("func pushDraftToViewModel()"),
            "Draft state must sync into the view model"
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
}
