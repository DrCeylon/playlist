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

    func testBackgroundProbeResumesWithoutConfirmManualAcquisitionGuard() throws {
        let source = try String(contentsOf: importViewModelSourceURL(), encoding: .utf8)
        XCTAssertTrue(source.contains("resumeImportAfterPositiveProbe"))
        XCTAssertTrue(source.contains("CALL resumeImportAfterPositiveProbe() from background probe"))
        XCTAssertFalse(source.contains("if probe.found {\n                await confirmManualAcquisition()"))
    }

    func testEarlyTerminalFailedPathsClearActiveImportToken() throws {
        let source = try String(contentsOf: importViewModelSourceURL(), encoding: .utf8)
        XCTAssertNotNil(
            source.range(
                of: #"playlist source introuvable\.\"\)\s*\n\s*activeImportToken = nil"#,
                options: .regularExpression
            )
        )
        XCTAssertNotNil(
            source.range(
                of: #"Session d'import introuvable\.\"\)\s*\n\s*activeImportToken = nil"#,
                options: .regularExpression
            )
        )
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
