import XCTest

final class ManualAcquisitionWorkflowArchitectureTests: XCTestCase {
    func testImportViewModelDelegatesManualWorkflowToCoordinator() throws {
        let source = try String(contentsOf: importViewModelSourceURL(), encoding: .utf8)
        XCTAssertTrue(source.contains("ManualAcquisitionWorkflowCoordinator"))
        XCTAssertTrue(source.contains("syncManualWorkflow"))
        XCTAssertFalse(source.contains("updateManualStatus"))
        XCTAssertFalse(source.contains("isContinuingManual = true"))
        XCTAssertTrue(source.contains("manualWorkflow.snapshot.isBusy"))
    }

    func testManualAcquisitionCardReflectsWorkflowState() throws {
        let source = try String(contentsOf: manualAcquisitionCardSourceURL(), encoding: .utf8)
        XCTAssertTrue(source.contains("status.phase.userFacingStep"))
        XCTAssertTrue(source.contains("elapsedSincePhaseEnteredLabel"))
        XCTAssertTrue(source.contains("nextStepHint"))
    }

    private func manualAcquisitionCardSourceURL() -> URL {
        sourceRoot().appendingPathComponent("Components/ManualAcquisitionCard.swift")
    }

    private func importViewModelSourceURL() -> URL {
        sourceRoot().appendingPathComponent("ViewModels/ImportViewModel.swift")
    }

    private func sourceRoot() -> URL {
        URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/ResonanceMac")
    }
}
