import Foundation

// MARK: - Workflow phase (single source of truth)

public enum ManualAcquisitionWorkflowPhase: String, Sendable, Equatable, Codable {
    case waitingForUser = "waiting_for_user"
    case verifyingLibrary = "verifying_library"
    case trackFound = "track_found"
    case updatingIdentityCache = "updating_identity_cache"
    case resumingImport = "resuming_import"
    case deliveringPlaylist = "delivering_playlist"
    case completed = "completed"
    case failed = "failed"
    case checkpointExpired = "checkpoint_expired"

    public var userFacingStep: String {
        switch self {
        case .waitingForUser:
            return "En attente d'ajout manuel"
        case .verifyingLibrary:
            return "Recherche dans la bibliothèque Music.app…"
        case .trackFound:
            return "Morceau détecté — reprise de l'import…"
        case .updatingIdentityCache:
            return "Mise à jour du cache identité…"
        case .resumingImport:
            return "Reprise après ajout manuel…"
        case .deliveringPlaylist:
            return "Synchronisation avec Music.app…"
        case .completed:
            return "Import terminé"
        case .failed:
            return "Erreur technique"
        case .checkpointExpired:
            return "Session expirée"
        }
    }

    public var nextStepHint: String {
        switch self {
        case .waitingForUser:
            return "Ajoutez le morceau dans Music.app, puis cliquez sur continuer."
        case .verifyingLibrary:
            return "Vérification en cours — patientez quelques secondes."
        case .trackFound, .resumingImport, .deliveringPlaylist:
            return "Import en cours — suivez la progression ci-dessus."
        case .completed:
            return "Consultez le rapport d'import."
        case .failed:
            return "Corrigez le problème indiqué puis réessayez."
        case .checkpointExpired:
            return "Relancez l'import depuis l'aperçu ou l'historique."
        case .updatingIdentityCache:
            return "Confirmation de la présence bibliothèque…"
        }
    }
}

public enum ManualAcquisitionWorkflow {
    private static let allowedTransitions: [ManualAcquisitionWorkflowPhase: Set<ManualAcquisitionWorkflowPhase>] = [
        .waitingForUser: [.verifyingLibrary, .resumingImport, .checkpointExpired, .failed],
        .verifyingLibrary: [.trackFound, .waitingForUser, .checkpointExpired, .failed, .updatingIdentityCache],
        .trackFound: [.updatingIdentityCache, .resumingImport, .failed],
        .updatingIdentityCache: [.trackFound, .resumingImport, .waitingForUser, .failed],
        .resumingImport: [.deliveringPlaylist, .waitingForUser, .completed, .failed, .checkpointExpired],
        .deliveringPlaylist: [.completed, .failed, .waitingForUser],
        .completed: [],
        .failed: [.waitingForUser],
        .checkpointExpired: [.waitingForUser],
    ]

    public static func canTransition(from current: ManualAcquisitionWorkflowPhase, to target: ManualAcquisitionWorkflowPhase) -> Bool {
        if current == target { return true }
        return allowedTransitions[current, default: []].contains(target)
    }

    public static func assertTransition(from current: ManualAcquisitionWorkflowPhase, to target: ManualAcquisitionWorkflowPhase) {
        guard canTransition(from: current, to: target) else {
            preconditionFailure("Illegal manual acquisition transition: \(current.rawValue) → \(target.rawValue)")
        }
    }
}

// MARK: - Coordinator (UI orchestration SSOT)

public struct ManualAcquisitionWorkflowSnapshot: Equatable, Sendable {
    public var phase: ManualAcquisitionWorkflowPhase
    public var uiStatus: ManualAcquisitionUIStatus
    public var pollStatus: String
    public var architectDiagnostics: String?
    public var shouldPoll: Bool
    public var isBusy: Bool

    public init(
        phase: ManualAcquisitionWorkflowPhase = .waitingForUser,
        uiStatus: ManualAcquisitionUIStatus = ManualAcquisitionUIStatus(),
        pollStatus: String = "",
        architectDiagnostics: String? = nil,
        shouldPoll: Bool = false,
        isBusy: Bool = false
    ) {
        self.phase = phase
        self.uiStatus = uiStatus
        self.pollStatus = pollStatus
        self.architectDiagnostics = architectDiagnostics
        self.shouldPoll = shouldPoll
        self.isBusy = isBusy
    }
}

public enum ManualAcquisitionWorkflowAction: Equatable, Sendable {
    case none
    case resumeImport(importSessionID: String)
    case finishImport(ImportResultState)
    case failScreen(String)
}

@MainActor
public final class ManualAcquisitionWorkflowCoordinator {
    public private(set) var snapshot: ManualAcquisitionWorkflowSnapshot
    public private(set) var phase: ManualAcquisitionWorkflowPhase

    private var phaseEnteredAt = Date()

    public init(snapshot: ManualAcquisitionWorkflowSnapshot = ManualAcquisitionWorkflowSnapshot()) {
        self.snapshot = snapshot
        self.phase = snapshot.phase
    }

    public func enterWaiting(
        importSessionID: String,
        canResume: Bool,
        fromHistory: Bool
    ) -> ManualAcquisitionWorkflowSnapshot {
        transition(to: .waitingForUser)
        let advice = canResume
            ? (fromHistory
                ? "Ajoutez le morceau dans Music.app si nécessaire, puis cliquez sur continuer."
                : "Ajoutez le morceau dans Music.app, puis cliquez sur continuer.")
            : "Relancez l'import depuis l'aperçu."
        let poll = canResume
            ? (fromHistory
                ? "Reprise depuis l'historique — ajoutez le morceau dans Music.app si nécessaire."
                : "")
            : "La session d'import a expiré. Relancez l'import depuis l'aperçu."
        snapshot = ManualAcquisitionWorkflowSnapshot(
            phase: phase,
            uiStatus: ManualAcquisitionUIStatus(
                currentStep: phase.userFacingStep,
                lastVerificationResult: "",
                userAdvice: advice,
                backendMessage: canResume ? nil : poll
            ),
            pollStatus: poll,
            shouldPoll: canResume,
            isBusy: false
        )
        _ = importSessionID
        return snapshot
    }

    public func reset() {
        transition(to: .waitingForUser)
        snapshot = ManualAcquisitionWorkflowSnapshot()
    }

    public func beginUserConfirmation(at clickTime: Date = .now) -> ManualAcquisitionWorkflowSnapshot {
        ManualContinueTrace.log("ENTER ManualAcquisitionWorkflowCoordinator.beginUserConfirmation()")
        guard !snapshot.isBusy else {
            ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.beginUserConfirmation() — already busy")
            return snapshot
        }
        transition(to: .verifyingLibrary)
        snapshot.isBusy = true
        snapshot.phase = phase
        snapshot.pollStatus = "Vérification lancée à \(ManualAcquisitionUIStatus.formattedClickTime(clickTime)) — recherche dans Music.app…"
        snapshot.uiStatus = ManualAcquisitionUIStatus(
            phase: phase,
            lastUserClickAt: clickTime,
            phaseEnteredAt: phaseEnteredAt,
            currentStep: "Recherche dans la bibliothèque Music.app…",
            lastVerificationResult: "",
            userAdvice: "Vérification en cours — patientez quelques secondes.",
            lastProbeStartedAt: clickTime
        )
        snapshot.shouldPoll = false
        ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.beginUserConfirmation() phase=\(phase.rawValue)")
        return snapshot
    }

    public func beginBackgroundProbe() -> ManualAcquisitionWorkflowSnapshot {
        ManualContinueTrace.log("ENTER ManualAcquisitionWorkflowCoordinator.beginBackgroundProbe()")
        guard !snapshot.isBusy, phase == .waitingForUser else { return snapshot }
        transition(to: .verifyingLibrary)
        let startedAt = Date()
        snapshot.uiStatus.lastProbeStartedAt = startedAt
        snapshot.uiStatus.currentStep = "Vérification automatique de la bibliothèque…"
        snapshot.uiStatus.phase = phase
        snapshot.uiStatus.phaseEnteredAt = phaseEnteredAt
        ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.beginBackgroundProbe() phase=\(phase.rawValue)")
        return snapshot
    }

    public func applyProbeResult(
        _ probe: ManualAcquisitionProbeResult,
        finishedAt: Date = .now,
        userInitiated: Bool
    ) -> (snapshot: ManualAcquisitionWorkflowSnapshot, action: ManualAcquisitionWorkflowAction) {
        ManualContinueTrace.log("ENTER ManualAcquisitionWorkflowCoordinator.applyProbeResult(found=\(probe.found), userInitiated=\(userInitiated))")
        let startedAt = probe.diagnostics?.probeStartedAt ?? snapshot.uiStatus.lastProbeStartedAt ?? finishedAt
        let durationMs = probe.diagnostics?.probeDurationMs
            ?? Int(finishedAt.timeIntervalSince(startedAt) * 1000)

        var architectLines: [String] = []
        if let workflowPhase = probe.workflowPhase, !workflowPhase.isEmpty {
            architectLines.append("workflow_phase: \(workflowPhase)")
        }
        if let errorCode = probe.errorCode, !errorCode.isEmpty {
            architectLines.append("backend_error_code: \(errorCode)")
        }
        if !probe.message.isEmpty {
            architectLines.append("backend_message: \(probe.message)")
        }
        if let summary = probe.architectSummary {
            architectLines.append(summary)
        }
        snapshot.architectDiagnostics = architectLines.isEmpty ? nil : architectLines.joined(separator: "\n")

        snapshot.uiStatus.lastProbeFinishedAt = finishedAt
        snapshot.uiStatus.lastProbeDurationMs = durationMs
        snapshot.uiStatus.backendMessage = probe.message
        snapshot.uiStatus.backendErrorCode = probe.errorCode

        if probe.errorCode == "checkpoint_missing" {
            transition(to: .checkpointExpired)
            snapshot.uiStatus.phase = phase
            snapshot.uiStatus.phaseEnteredAt = phaseEnteredAt
            snapshot.uiStatus.currentStep = "Session expirée"
            snapshot.uiStatus.lastVerificationResult = probe.message
            snapshot.uiStatus.userAdvice = "Relancez l'import depuis l'aperçu ou l'historique."
            snapshot.pollStatus = probe.message
            snapshot.shouldPoll = false
            snapshot.isBusy = false
            snapshot.phase = phase
            ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.applyProbeResult() action=none phase=checkpoint_expired")
            return (snapshot, .none)
        }

        if let probeError = probe.diagnostics?.probeError, !probeError.isEmpty {
            transition(to: .failed)
            snapshot.uiStatus.phase = phase
            snapshot.uiStatus.phaseEnteredAt = phaseEnteredAt
            snapshot.uiStatus.currentStep = "Erreur technique"
            snapshot.uiStatus.lastVerificationResult = probe.message
            snapshot.uiStatus.userAdvice = "Vérifiez Music.app et les autorisations Automatisation, puis réessayez."
            snapshot.pollStatus = probe.message
            snapshot.shouldPoll = true
            snapshot.isBusy = false
            snapshot.phase = phase
            ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.applyProbeResult() action=none phase=failed probe_error=\(probeError)")
            return (snapshot, .none)
        }

        if probe.found {
            transition(to: .trackFound)
            let message = probe.message.isEmpty ? "Morceau détecté — reprise de l'import…" : probe.message
            snapshot.uiStatus.phase = phase
            snapshot.uiStatus.phaseEnteredAt = phaseEnteredAt
            snapshot.uiStatus.currentStep = userInitiated
                ? "Morceau détecté — reprise de l'import…"
                : "Morceau détecté — reprise automatique…"
            snapshot.uiStatus.lastVerificationResult = message
            snapshot.uiStatus.userAdvice = "Reprise de l'import en cours."
            snapshot.pollStatus = message
            snapshot.isBusy = true
            snapshot.phase = phase
            if let sessionID = probe.diagnostics?.importSessionID, !sessionID.isEmpty {
                ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.applyProbeResult() action=resumeImport session=\(sessionID)")
                return (snapshot, .resumeImport(importSessionID: sessionID))
            }
            ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.applyProbeResult() action=none phase=track_found (missing session id)")
            return (snapshot, .none)
        }

        transition(to: .waitingForUser)
        let message = probe.message.isEmpty
            ? "Morceau pas encore détecté dans la bibliothèque. Vérifiez qu'il a bien été ajouté dans Music.app, puis réessayez."
            : probe.message
        snapshot.uiStatus.phase = phase
        snapshot.uiStatus.phaseEnteredAt = phaseEnteredAt
        snapshot.uiStatus.currentStep = "Morceau non détecté"
        snapshot.uiStatus.lastVerificationResult = message
        snapshot.uiStatus.userAdvice = userInitiated
            ? "Ajoutez le morceau dans Music.app, puis cliquez à nouveau sur continuer."
            : "Ajoutez le morceau dans Music.app, puis cliquez sur continuer."
        snapshot.pollStatus = message
        snapshot.shouldPoll = true
        snapshot.isBusy = false
        snapshot.phase = phase
        ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.applyProbeResult() action=none phase=waiting_for_user")
        return (snapshot, .none)
    }

    public func beginResumingImport() -> ManualAcquisitionWorkflowSnapshot {
        ManualContinueTrace.log("ENTER ManualAcquisitionWorkflowCoordinator.beginResumingImport()")
        transition(to: .resumingImport)
        snapshot.phase = phase
        snapshot.uiStatus.phase = phase
        snapshot.uiStatus.phaseEnteredAt = phaseEnteredAt
        snapshot.uiStatus.currentStep = "Reprise après ajout manuel…"
        snapshot.uiStatus.userAdvice = "Import en cours — suivez la progression ci-dessus."
        snapshot.isBusy = true
        ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.beginResumingImport() phase=\(phase.rawValue)")
        return snapshot
    }

    public func applyContinueResult(_ result: ImportResultState) -> (snapshot: ManualAcquisitionWorkflowSnapshot, action: ManualAcquisitionWorkflowAction) {
        ManualContinueTrace.log("ENTER ManualAcquisitionWorkflowCoordinator.applyContinueResult(phase=\(result.phase.rawValue))")
        snapshot.isBusy = false
        if result.phase == .waitingForManualAcquisition {
            transition(to: .waitingForUser)
            let message = "Morceau pas encore détecté dans la bibliothèque. Vérifiez qu'il a bien été ajouté dans Music.app, puis réessayez."
            snapshot.uiStatus.phase = phase
            snapshot.uiStatus.phaseEnteredAt = phaseEnteredAt
            snapshot.uiStatus.currentStep = "Morceau non détecté"
            snapshot.uiStatus.lastVerificationResult = message
            snapshot.uiStatus.userAdvice = "Ajoutez le morceau dans Music.app, puis cliquez à nouveau sur continuer."
            snapshot.pollStatus = message
            snapshot.shouldPoll = true
            snapshot.phase = phase
            ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.applyContinueResult() action=none still waiting")
            return (snapshot, .none)
        }
        transition(to: .completed)
        snapshot.phase = phase
        snapshot.shouldPoll = false
        ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.applyContinueResult() action=finishImport")
        return (snapshot, .finishImport(result))
    }

    public func applyBridgeError(_ message: String, architectDetail: String?) -> ManualAcquisitionWorkflowSnapshot {
        ManualContinueTrace.log("ENTER ManualAcquisitionWorkflowCoordinator.applyBridgeError(\(message))")
        transition(to: .failed)
        snapshot.uiStatus.phase = phase
        snapshot.uiStatus.phaseEnteredAt = phaseEnteredAt
        snapshot.uiStatus.currentStep = "Erreur technique"
        snapshot.uiStatus.lastVerificationResult = message
        snapshot.uiStatus.userAdvice = "Utilisez le bouton continuer pour relancer la vérification."
        snapshot.uiStatus.backendMessage = message
        snapshot.uiStatus.backendErrorCode = "bridge_error"
        snapshot.pollStatus = message
        snapshot.architectDiagnostics = architectDetail
        snapshot.shouldPoll = true
        snapshot.isBusy = false
        snapshot.phase = phase
        ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.applyBridgeError() phase=failed")
        return snapshot
    }

    private func transition(to target: ManualAcquisitionWorkflowPhase) {
        ManualAcquisitionWorkflow.assertTransition(from: phase, to: target)
        phase = target
        phaseEnteredAt = Date()
    }
}
