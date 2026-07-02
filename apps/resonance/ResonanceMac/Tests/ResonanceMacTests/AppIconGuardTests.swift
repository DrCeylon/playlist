import XCTest

final class AppIconGuardTests: XCTestCase {
    func testAppIconAssetsExist() throws {
        let resources = resourcesRoot()
        let iconset = resources.appendingPathComponent("AppIcon.iconset")
        let assets = resources.appendingPathComponent("Assets")

        XCTAssertTrue(
            FileManager.default.fileExists(atPath: assets.appendingPathComponent("AppIcon-512.png").path),
            "Dock/runtime icon PNG must be bundled"
        )
        XCTAssertTrue(
            FileManager.default.fileExists(atPath: iconset.appendingPathComponent("icon_512x512@2x.png").path),
            "macOS iconset must include 1024px master"
        )
        XCTAssertTrue(
            FileManager.default.fileExists(atPath: resources.appendingPathComponent("Info.plist").path),
            "Info.plist required for .app packaging"
        )
    }

    func testApplicationIconConfiguratorSourceExists() throws {
        let source = try String(
            contentsOf: supportSourceURL(),
            encoding: .utf8
        )
        XCTAssertTrue(source.contains("ApplicationIconConfigurator"))
        XCTAssertTrue(source.contains("applicationIconImage"))
    }

    private func resourcesRoot() -> URL {
        URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Resources")
    }

    private func supportSourceURL() -> URL {
        URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/ResonanceMac/Support/ApplicationIconConfigurator.swift")
    }
}
