import Foundation
import ResonanceCore
@testable import ResonanceMac
import XCTest

final class ResonancePathsTests: XCTestCase {
    private var fileManager: FileManager { .default }

    // MARK: - Configured environment

    func testRepoRootFromConfiguredEnvironment() throws {
        let repoRoot = try makeTemporaryRepoRoot()
        defer { removeTemporaryItem(at: repoRoot) }

        let found = ResonancePaths.repoRoot(
            fileManager: fileManager,
            environment: ["RESONANCE_REPO_ROOT": repoRoot.path]
        )

        XCTAssertNotNil(found)
        XCTAssertEqual(found?.standardizedFileURL, repoRoot.standardizedFileURL)
        XCTAssertTrue(repoMarkerExists(at: found!))
    }

    func testRepoRootIgnoresConfiguredEnvironmentWithoutMarker() throws {
        let emptyDirectory = try makeTemporaryDirectory()
        defer { removeTemporaryItem(at: emptyDirectory) }

        let found = ResonancePaths.repoRoot(
            fileManager: fileManager,
            environment: ["RESONANCE_REPO_ROOT": emptyDirectory.path]
        )

        if let discovered = discoverRepositoryRootFromWorkingTree() {
            XCTAssertEqual(found?.standardizedFileURL, discovered.standardizedFileURL)
        } else {
            XCTAssertNil(found)
        }
    }

    // MARK: - Python resolution

    func testResolvePythonPrefersVenvWhenPresent() throws {
        let repoRoot = try makeTemporaryRepoRoot()
        defer { removeTemporaryItem(at: repoRoot) }

        let venvPython = repoRoot
            .appendingPathComponent(".venv/bin/python", isDirectory: false)
        try fileManager.createDirectory(
            at: venvPython.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        try makeExecutableFile(at: venvPython)

        let python = ResonancePaths.resolvePythonExecutable(
            repoRoot: repoRoot,
            fileManager: fileManager
        )

        XCTAssertEqual(
            URL(fileURLWithPath: python).standardizedFileURL,
            venvPython.standardizedFileURL
        )
        XCTAssertTrue(fileManager.isExecutableFile(atPath: python))
    }

    func testResolvePythonFallsBackToSystemPythonWhenVenvMissing() throws {
        let repoRoot = try makeTemporaryRepoRoot()
        defer { removeTemporaryItem(at: repoRoot) }

        let python = ResonancePaths.resolvePythonExecutable(
            repoRoot: repoRoot,
            fileManager: fileManager
        )

        XCTAssertFalse(python.isEmpty)
        XCTAssertTrue(fileManager.isExecutableFile(atPath: python))
    }

    // MARK: - Automatic configuration

    func testAutomaticConfigurationUsesRepoRoot() throws {
        let repoRoot = try makeTemporaryRepoRoot()
        defer { removeTemporaryItem(at: repoRoot) }

        let config = PythonEngineBridgeConfiguration.automatic(
            fileManager: fileManager,
            environment: ["RESONANCE_REPO_ROOT": repoRoot.path]
        )

        XCTAssertNotNil(config)
        XCTAssertEqual(config?.workingDirectory.standardizedFileURL, repoRoot.standardizedFileURL)
        XCTAssertTrue(fileManager.fileExists(atPath: config!.workingDirectory.path))
        XCTAssertTrue(repoMarkerExists(at: config!.workingDirectory))
        XCTAssertFalse(config!.pythonExecutable.isEmpty)
        XCTAssertTrue(fileManager.isExecutableFile(atPath: config!.pythonExecutable))
    }

    func testAutomaticConfigurationNilWhenRepoNotDiscoverable() throws {
        let isolatedDirectory = try makeTemporaryDirectory()
        defer { removeTemporaryItem(at: isolatedDirectory) }

        let previousDirectory = fileManager.currentDirectoryPath
        defer { _ = fileManager.changeCurrentDirectoryPath(previousDirectory) }
        XCTAssertTrue(fileManager.changeCurrentDirectoryPath(isolatedDirectory.path))

        let config = PythonEngineBridgeConfiguration.automatic(
            fileManager: fileManager,
            environment: [
                "RESONANCE_REPO_ROOT": isolatedDirectory.path,
                "RESONANCE_EXECUTABLE_PATH": isolatedDirectory.path,
            ]
        )

        XCTAssertNil(config)
    }

    // MARK: - Discovery

    func testRepoRootWalksUpFromNestedDirectory() throws {
        let repoRoot = try makeTemporaryRepoRoot()
        defer { removeTemporaryItem(at: repoRoot) }

        let nestedDirectory = repoRoot
            .appendingPathComponent("apps/resonance/.build/debug", isDirectory: true)
        try fileManager.createDirectory(at: nestedDirectory, withIntermediateDirectories: true)

        let previousDirectory = fileManager.currentDirectoryPath
        defer { _ = fileManager.changeCurrentDirectoryPath(previousDirectory) }
        XCTAssertTrue(fileManager.changeCurrentDirectoryPath(nestedDirectory.path))

        let found = ResonancePaths.repoRoot(
            fileManager: fileManager,
            environment: [
                "RESONANCE_EXECUTABLE_PATH": nestedDirectory.path,
            ]
        )

        XCTAssertNotNil(found)
        XCTAssertEqual(found?.standardizedFileURL, repoRoot.standardizedFileURL)
        XCTAssertTrue(repoMarkerExists(at: found!))
    }

    func testRepoRootDiscoversCurrentRepositoryWhenRunFromClone() throws {
        guard let expectedRoot = discoverRepositoryRootFromWorkingTree() else {
            throw XCTSkip("Requires running inside a playlist repository clone.")
        }

        let found = ResonancePaths.repoRoot(fileManager: fileManager, environment: [:])

        XCTAssertNotNil(found)
        XCTAssertEqual(found?.standardizedFileURL, expectedRoot.standardizedFileURL)
        XCTAssertTrue(repoMarkerExists(at: found!))
    }

    // MARK: - Helpers

    private func makeTemporaryDirectory() throws -> URL {
        let directory = fileManager.temporaryDirectory
            .appendingPathComponent("resonance-paths-\(UUID().uuidString)", isDirectory: true)
        try fileManager.createDirectory(at: directory, withIntermediateDirectories: true)
        return directory
    }

    private func makeTemporaryRepoRoot() throws -> URL {
        let root = try makeTemporaryDirectory()
        try fileManager.createDirectory(
            at: root.appendingPathComponent("playlist_builder", isDirectory: true),
            withIntermediateDirectories: true
        )
        return root
    }

    private func makeExecutableFile(at url: URL) throws {
        let content = Data("#!/bin/sh\nexit 0\n".utf8)
        try content.write(to: url)
        try fileManager.setAttributes(
            [.posixPermissions: NSNumber(value: Int16(0o755))],
            ofItemAtPath: url.path
        )
    }

    private func repoMarkerExists(at url: URL) -> Bool {
        fileManager.fileExists(
            atPath: url.appendingPathComponent("playlist_builder", isDirectory: true).path
        )
    }

    private func removeTemporaryItem(at url: URL) {
        try? fileManager.removeItem(at: url)
    }

    private func discoverRepositoryRootFromWorkingTree() -> URL? {
        var candidate = URL(fileURLWithPath: fileManager.currentDirectoryPath, isDirectory: true)
        for _ in 0..<12 {
            if repoMarkerExists(at: candidate) {
                return candidate.standardizedFileURL
            }
            let parent = candidate.deletingLastPathComponent()
            if parent.path == candidate.path {
                break
            }
            candidate = parent
        }
        return nil
    }
}
