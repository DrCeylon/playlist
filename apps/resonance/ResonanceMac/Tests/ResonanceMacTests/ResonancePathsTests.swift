import ResonanceCore
@testable import ResonanceMac
import XCTest

final class ResonancePathsTests: XCTestCase {
    func testRepoRootFromConfiguredEnvironment() {
        let root = URL(fileURLWithPath: "/workspace", isDirectory: true)
        let found = ResonancePaths.repoRoot(
            fileManager: .default,
            environment: ["RESONANCE_REPO_ROOT": root.path]
        )
        XCTAssertEqual(found?.path, root.path)
    }

    func testResolvePythonPrefersVenvWhenPresent() {
        let root = URL(fileURLWithPath: "/workspace", isDirectory: true)
        let python = ResonancePaths.resolvePythonExecutable(repoRoot: root)
        if FileManager.default.isExecutableFile(atPath: root.appendingPathComponent(".venv/bin/python").path) {
            XCTAssertTrue(python.hasSuffix(".venv/bin/python"))
        } else {
            XCTAssertFalse(python.isEmpty)
        }
    }

    func testAutomaticConfigurationUsesRepoRoot() {
        let config = PythonEngineBridgeConfiguration.automatic(
            environment: ["RESONANCE_REPO_ROOT": "/workspace"]
        )
        XCTAssertNotNil(config)
        XCTAssertEqual(config?.workingDirectory.path, "/workspace")
    }

    func testAutomaticConfigurationNilWhenRepoMissing() {
        let config = PythonEngineBridgeConfiguration.automatic(
            fileManager: .default,
            environment: ["RESONANCE_REPO_ROOT": "/tmp/no-such-repo"]
        )
        XCTAssertNil(config)
    }
}
