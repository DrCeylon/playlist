import ResonanceCore
@testable import ResonanceMac
import XCTest

final class ImportErrorHumanizerTests: XCTestCase {
    func testHumanizesCocoaJSONError() {
        let error = NSError(
            domain: NSCocoaErrorDomain,
            code: 3840,
            userInfo: [NSLocalizedDescriptionKey: "The data couldn't be read because it isn't in the correct format."]
        )
        let message = ImportErrorHumanizer.userMessage(for: error)
        XCTAssertFalse(message.contains("couldn't be read"))
        XCTAssertTrue(message.contains("Réponse bridge invalide"))
    }

    func testHumanizesAutomationPermissionMessage() {
        let message = ImportErrorHumanizer.humanizeBridgeMessage("Not authorized to send Apple events (-1743)")
        XCTAssertTrue(message.contains("Automatisation"))
    }

    func testPlaylistImportInvalidResponseMessage() {
        let message = ImportErrorHumanizer.message(for: .invalidResponse)
        XCTAssertTrue(message.contains("Réponse bridge invalide"))
    }
}

final class ImportPerformanceGuardTests: XCTestCase {
    func testImportViewModelSourceDoesNotAppendEveryStderrLine() throws {
        let path = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/ResonanceMac/ViewModels/ImportViewModel.swift")
        let source = try String(contentsOf: path, encoding: .utf8)
        XCTAssertTrue(source.contains("shouldSurfaceDiagnostic"))
        XCTAssertTrue(source.contains("maxVisibleDiagnostics"))
        XCTAssertFalse(source.contains("|| message.contains(\"resonance-import:\")"))
    }

    func testBridgeServiceDoesNotForwardStderrToUIEvents() throws {
        let path = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/ResonanceMac/Services/PythonEngineBridgeService.swift")
        let source = try String(contentsOf: path, encoding: .utf8)
        XCTAssertTrue(source.contains("bridgeServiceLogger.debug"))
        XCTAssertFalse(source.contains("event: .diagnostic,\n                            payload: [\"message\": .string(line)]"))
    }
}
