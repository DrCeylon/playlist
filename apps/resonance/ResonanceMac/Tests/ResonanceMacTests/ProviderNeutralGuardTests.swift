import XCTest

final class ProviderNeutralGuardTests: XCTestCase {
    private let forbiddenTokens = [
        "AppleScript",
        "MusicKit",
        "persistent_id",
        "NSAppleScript",
        "ApplicationMusic",
    ]

    func testSwiftUIDoesNotExposeProviderSpecificBridgeDetails() throws {
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/ResonanceMac")

        let targets = ["Screens", "ViewModels"]
        var swiftFiles: [URL] = []
        for target in targets {
            swiftFiles.append(contentsOf: try Self.collectSwiftFiles(in: root.appendingPathComponent(target)))
        }
        XCTAssertFalse(swiftFiles.isEmpty)

        for file in swiftFiles {
            let source = try String(contentsOf: file, encoding: .utf8)
            for token in forbiddenTokens {
                XCTAssertFalse(
                    source.contains(token),
                    "Forbidden token \(token) found in \(file.lastPathComponent)"
                )
            }
        }
    }

    private static func collectSwiftFiles(in root: URL) throws -> [URL] {
        let manager = FileManager.default
        guard let enumerator = manager.enumerator(
            at: root,
            includingPropertiesForKeys: nil,
            options: [.skipsHiddenFiles]
        ) else {
            return []
        }

        var files: [URL] = []
        for case let url as URL in enumerator {
            if url.pathExtension == "swift",
               !url.pathComponents.contains(".build"),
               !url.pathComponents.contains("DerivedData") {
                files.append(url)
            }
        }
        return files
    }
}
