import XCTest
@testable import ResonanceCore

final class ManualAcquisitionWorkflowTests: XCTestCase {
    func testIllegalTransitionsAreRejected() {
        XCTAssertTrue(ManualAcquisitionWorkflow.canTransition(from: .waitingForUser, to: .verifyingLibrary))
        XCTAssertFalse(ManualAcquisitionWorkflow.canTransition(from: .completed, to: .verifyingLibrary))
        XCTAssertFalse(ManualAcquisitionWorkflow.canTransition(from: .waitingForUser, to: .completed))
    }

    func testCoordinatorOrchestratesUserConfirmationFlow() async {
        let confirming: ManualAcquisitionWorkflowSnapshot = await MainActor.run {
            let coordinator = ManualAcquisitionWorkflowCoordinator()
            _ = coordinator.enterWaiting(importSessionID: "session-1", canResume: true, fromHistory: false)
            return coordinator.beginUserConfirmation(at: Date(timeIntervalSince1970: 1_700_000_000))
        }
        XCTAssertEqual(confirming.phase, .verifyingLibrary)
        XCTAssertEqual(confirming.uiStatus.currentStep, "Recherche dans la bibliothèque Music.app…")
        XCTAssertTrue(confirming.isBusy)

        let probe = ManualAcquisitionProbeResult(
            found: false,
            message: "Morceau pas encore détecté dans la bibliothèque. Vérifiez qu'il a bien été ajouté dans Music.app, puis réessayez.",
            errorCode: "track_not_found",
            workflowPhase: ManualAcquisitionWorkflowPhase.waitingForUser.rawValue,
            diagnostics: ManualAcquisitionProbeDiagnostics(importSessionID: "session-1")
        )
        let (snapshot, action): (ManualAcquisitionWorkflowSnapshot, ManualAcquisitionWorkflowAction) = await MainActor.run {
            let coordinator = ManualAcquisitionWorkflowCoordinator()
            _ = coordinator.enterWaiting(importSessionID: "session-1", canResume: true, fromHistory: false)
            _ = coordinator.beginUserConfirmation(at: Date(timeIntervalSince1970: 1_700_000_000))
            return coordinator.applyProbeResult(probe, userInitiated: true)
        }
        XCTAssertEqual(action, .none)
        XCTAssertEqual(snapshot.phase, .waitingForUser)
        XCTAssertEqual(snapshot.uiStatus.currentStep, "Morceau non détecté")
        XCTAssertTrue(snapshot.shouldPoll)
        XCTAssertFalse(snapshot.isBusy)
    }

    func testCoordinatorResumesWhenTrackFound() async {
        let probe = ManualAcquisitionProbeResult(
            found: true,
            message: "Morceau détecté dans la bibliothèque Music.app.",
            diagnostics: ManualAcquisitionProbeDiagnostics(importSessionID: "session-2")
        )
        let (snapshot, action): (ManualAcquisitionWorkflowSnapshot, ManualAcquisitionWorkflowAction) = await MainActor.run {
            let coordinator = ManualAcquisitionWorkflowCoordinator()
            _ = coordinator.enterWaiting(importSessionID: "session-2", canResume: true, fromHistory: false)
            _ = coordinator.beginUserConfirmation()
            return coordinator.applyProbeResult(probe, userInitiated: true)
        }
        XCTAssertEqual(snapshot.phase, .trackFound)
        if case .resumeImport(let sessionID) = action {
            XCTAssertEqual(sessionID, "session-2")
        } else {
            XCTFail("Expected resumeImport action")
        }
    }

    func testHistoryAndFreshImportShareCoordinatorType() async {
        let (fresh, history): (ManualAcquisitionWorkflowSnapshot, ManualAcquisitionWorkflowSnapshot) = await MainActor.run {
            let freshCoordinator = ManualAcquisitionWorkflowCoordinator()
            let historyCoordinator = ManualAcquisitionWorkflowCoordinator()
            let fresh = freshCoordinator.enterWaiting(importSessionID: "a", canResume: true, fromHistory: false)
            let history = historyCoordinator.enterWaiting(importSessionID: "b", canResume: true, fromHistory: true)
            return (fresh, history)
        }

        XCTAssertEqual(fresh.phase, .waitingForUser)
        XCTAssertEqual(history.phase, .waitingForUser)
        XCTAssertTrue(history.pollStatus.contains("historique"))
    }

    func testResetFromCompletedReinitializesSessionWithoutBusinessTransition() async {
        await MainActor.run {
            let coordinator = ManualAcquisitionWorkflowCoordinator()
            driveCoordinatorToCompleted(coordinator, resultPhase: .partialSuccess)
            XCTAssertEqual(coordinator.phase, .completed)

            coordinator.reset()

            XCTAssertEqual(coordinator.phase, .waitingForUser)
            XCTAssertEqual(coordinator.snapshot, ManualAcquisitionWorkflowSnapshot())
            XCTAssertFalse(coordinator.snapshot.isBusy)
        }
    }

    func testResetAfterCompletedAllowsNewAcquisitionCycle() async {
        await MainActor.run {
            let coordinator = ManualAcquisitionWorkflowCoordinator()
            driveCoordinatorToCompleted(coordinator, resultPhase: .completed)
            coordinator.reset()

            let waiting = coordinator.enterWaiting(importSessionID: "session-2", canResume: true, fromHistory: false)
            XCTAssertEqual(waiting.phase, .waitingForUser)
            let confirming = coordinator.beginUserConfirmation()
            XCTAssertEqual(confirming.phase, .verifyingLibrary)
        }
    }

    func testCompletedToWaitingForUserRemainsIllegalBusinessTransition() {
        XCTAssertFalse(
            ManualAcquisitionWorkflow.canTransition(from: .completed, to: .waitingForUser),
            "Session reset must use reset(), not transition()"
        )
    }
}

@MainActor
private func driveCoordinatorToCompleted(
    _ coordinator: ManualAcquisitionWorkflowCoordinator,
    resultPhase: ImportPhase
) {
    _ = coordinator.enterWaiting(importSessionID: "session-1", canResume: true, fromHistory: false)
    _ = coordinator.beginUserConfirmation()
    let probe = ManualAcquisitionProbeResult(
        found: true,
        message: "Morceau détecté",
        diagnostics: ManualAcquisitionProbeDiagnostics(importSessionID: "session-1")
    )
    _ = coordinator.applyProbeResult(probe, userInitiated: true)
    _ = coordinator.beginResumingImport()
    _ = coordinator.applyContinueResult(ImportResultState(playlistName: "Demo", phase: resultPhase))
}
