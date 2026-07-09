import Foundation
import ResonanceCore

@MainActor
final class ImportViewModel: ObservableObject {
    enum ScreenState: Equatable {
        case idle
        case importing
        case waitingForManualAcquisition
        case report
        case failed(String)
    }

    @Published var screenState: ScreenState = .idle
    @Published var progress = ImportProgressSnapshot()
    @Published var manualPrompt: ManualAcquisitionPrompt?
    @Published var manualPollStatus = ""
    @Published var manualAcquisitionStatus = ManualAcquisitionUIStatus()
    @Published var report: ImportResultState?
    @Published var architectErrorDetail: String?
    @Published var architectManualDiagnostics: String?
    @Published private(set) var activeHistorySessionID: String = ""

    private let service: any PlaylistImportServing
    private let manualWorkflow = ManualAcquisitionWorkflowCoordinator()
    private var importSessionID: String?
    private var manualPollTask: Task<Void, Never>?
    private var importedGeneration: PlaylistGenerationResult?
    private var activeImportToken: UUID?

    init(service: any PlaylistImportServing = MockPlaylistImportService()) {
        self.service = service
    }

    var isContinuingManual: Bool { manualWorkflow.snapshot.isBusy }

    func importPlaylist(_ generationResult: PlaylistGenerationResult) async {
        importedGeneration = generationResult
        beginImport(
            playlistName: generationResult.playlistName,
            totalTracks: generationResult.trackCount,
            historySessionID: generationResult.historySessionID
        )
        guard let token = activeImportToken else { return }

        do {
            let result = try await service.importPlaylist(
                generationResult,
                onEvent: importEventHandler(for: token)
            )
            await flushPendingImportEvents()
            guard activeImportToken == token else { return }
            finishImport(with: result)
        } catch let error as PlaylistImportError {
            guard activeImportToken == token else { return }
            failImport(error)
        } catch {
            guard activeImportToken == token else { return }
            failImport(error)
        }
    }

    func retryImportTrack(at index: Int) async {
        guard let importedGeneration else {
            screenState = .failed("Impossible de réessayer : playlist source introuvable.")
            return
        }
        let existingOutcomes = report?.outcomes
        let resolvedHistorySessionID = activeHistorySessionID.isEmpty
            ? importedGeneration.historySessionID
            : activeHistorySessionID
        beginImport(
            playlistName: importedGeneration.playlistName,
            totalTracks: importedGeneration.trackCount,
            historySessionID: resolvedHistorySessionID
        )
        guard let token = activeImportToken else { return }
        mutateProgress { snapshot in
            snapshot.currentStep = "Nouvelle tentative pour un morceau…"
            snapshot.totalTracks = importedGeneration.trackCount
        }
        screenState = .importing

        do {
            let result = try await service.retryImportTracks(
                importedGeneration,
                trackIndices: [index],
                existingOutcomes: existingOutcomes,
                historySessionID: resolvedHistorySessionID.isEmpty ? nil : resolvedHistorySessionID,
                onEvent: importEventHandler(for: token)
            )
            await flushPendingImportEvents()
            guard activeImportToken == token else { return }
            finishImport(with: result)
        } catch let error as PlaylistImportError {
            guard activeImportToken == token else { return }
            failImport(error)
        } catch {
            guard activeImportToken == token else { return }
            failImport(error)
        }
    }

    func confirmManualAcquisition() async {
        ManualContinueTrace.log("ENTER confirmManualAcquisition()")
        guard !isContinuingManual else {
            ManualContinueTrace.log("EXIT confirmManualAcquisition() early — isContinuingManual=true")
            return
        }
        guard let importSessionID else {
            ManualContinueTrace.log("EXIT confirmManualAcquisition() early — importSessionID nil")
            screenState = .failed("Session d'import introuvable.")
            syncManualWorkflow(manualWorkflow.applyBridgeError(
                "Session d'import introuvable.",
                architectDetail: nil
            ))
            return
        }
        ManualContinueTrace.beginSession(importSessionID: importSessionID)
        let token = activeImportToken
        architectManualDiagnostics = nil
        stopManualPolling()
        ManualContinueTrace.log("CALL ManualAcquisitionWorkflowCoordinator.beginUserConfirmation()")
        syncManualWorkflow(manualWorkflow.beginUserConfirmation())
        ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.beginUserConfirmation()")
        mutateProgress { snapshot in
            snapshot.currentStep = manualAcquisitionStatus.currentStep
            snapshot.lastActivityAt = .now
        }
        await Task.yield()

        do {
            ManualContinueTrace.log("CALL PythonEngineBridgeService.probeManualAcquisition(importSessionID:)")
            let probe = try await service.probeManualAcquisition(importSessionID: importSessionID)
            ManualContinueTrace.log("RETURN PythonEngineBridgeService.probeManualAcquisition found=\(probe.found)")
            ManualContinueTrace.log("CALL ManualAcquisitionWorkflowCoordinator.applyProbeResult(userInitiated=true)")
            var (snapshot, action) = manualWorkflow.applyProbeResult(probe, userInitiated: true)
            ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.applyProbeResult action=\(String(describing: action))")
            syncManualWorkflow(snapshot)

            guard token == nil || token == activeImportToken else {
                ManualContinueTrace.log("EXIT confirmManualAcquisition() — stale import token after probe")
                return
            }

            if case .resumeImport(let sessionID) = action {
                await resumeImportAfterPositiveProbe(importSessionID: sessionID, token: token)
            } else if manualWorkflow.snapshot.shouldPoll {
                ManualContinueTrace.log("CALL startManualPolling() — probe not ready for resume")
                startManualPolling()
            }
            ManualContinueTrace.log("EXIT confirmManualAcquisition() success")
        } catch let error as PlaylistImportError {
            ManualContinueTrace.log("ERROR confirmManualAcquisition() PlaylistImportError: \(ImportErrorHumanizer.message(for: error))")
            guard token == nil || token == activeImportToken else { return }
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
            syncManualWorkflow(manualWorkflow.applyBridgeError(
                ImportErrorHumanizer.message(for: error),
                architectDetail: architectErrorDetail
            ))
            screenState = .waitingForManualAcquisition
            startManualPolling()
        } catch {
            ManualContinueTrace.log("ERROR confirmManualAcquisition() \(error.localizedDescription)")
            guard token == nil || token == activeImportToken else { return }
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
            syncManualWorkflow(manualWorkflow.applyBridgeError(
                ImportErrorHumanizer.userMessage(for: error),
                architectDetail: architectErrorDetail
            ))
            screenState = .waitingForManualAcquisition
            startManualPolling()
        }
    }

    /// Resumes import after a positive library probe. Not gated by `isContinuingManual` —
    /// background auto-resume and user-initiated resume both use this path once `resumeImport` is decided.
    func resumeImportAfterPositiveProbe(importSessionID sessionID: String, token: UUID?) async {
        ManualContinueTrace.log("ENTER resumeImportAfterPositiveProbe(sessionID:)")
        do {
            ManualContinueTrace.log("CALL ManualAcquisitionWorkflowCoordinator.beginResumingImport()")
            syncManualWorkflow(manualWorkflow.beginResumingImport())
            ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.beginResumingImport()")
            mutateProgress { snapshot in
                snapshot.currentStep = manualAcquisitionStatus.currentStep
                snapshot.lastActivityAt = .now
            }
            ManualContinueTrace.log("CALL PythonEngineBridgeService.continueManualAcquisition(importSessionID:)")
            guard let handlerToken = token ?? activeImportToken else {
                ManualContinueTrace.log("EXIT resumeImportAfterPositiveProbe() — missing import token for event handler")
                return
            }
            let result = try await service.continueManualAcquisition(
                importSessionID: sessionID,
                onEvent: importEventHandler(for: handlerToken)
            )
            ManualContinueTrace.log("RETURN PythonEngineBridgeService.continueManualAcquisition phase=\(result.phase.rawValue)")
            await flushPendingImportEvents()
            guard token == nil || token == activeImportToken else {
                ManualContinueTrace.log("EXIT resumeImportAfterPositiveProbe() — stale import token after continue")
                return
            }
            ManualContinueTrace.log("CALL ManualAcquisitionWorkflowCoordinator.applyContinueResult()")
            let (snapshot, action) = manualWorkflow.applyContinueResult(result)
            ManualContinueTrace.log("RETURN ManualAcquisitionWorkflowCoordinator.applyContinueResult action=\(String(describing: action))")
            syncManualWorkflow(snapshot)
            if case .finishImport(let importResult) = action {
                ManualContinueTrace.log("CALL finishImport(with:)")
                finishImport(with: importResult)
                ManualContinueTrace.log("RETURN finishImport(with:)")
            }
            ManualContinueTrace.log("EXIT resumeImportAfterPositiveProbe() success")
        } catch let error as PlaylistImportError {
            ManualContinueTrace.log("ERROR resumeImportAfterPositiveProbe() PlaylistImportError: \(ImportErrorHumanizer.message(for: error))")
            guard token == nil || token == activeImportToken else { return }
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
            syncManualWorkflow(manualWorkflow.applyBridgeError(
                ImportErrorHumanizer.message(for: error),
                architectDetail: architectErrorDetail
            ))
            screenState = .waitingForManualAcquisition
            startManualPolling()
        } catch {
            ManualContinueTrace.log("ERROR resumeImportAfterPositiveProbe() \(error.localizedDescription)")
            guard token == nil || token == activeImportToken else { return }
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
            syncManualWorkflow(manualWorkflow.applyBridgeError(
                ImportErrorHumanizer.userMessage(for: error),
                architectDetail: architectErrorDetail
            ))
            screenState = .waitingForManualAcquisition
            startManualPolling()
        }
    }

    func restoreManualAcquisition(
        from report: ImportResultState,
        generation: PlaylistGenerationResult?,
        historySessionID: String = ""
    ) {
        importedGeneration = generation
        activeImportToken = UUID()
        activeHistorySessionID = historySessionID.isEmpty ? report.historySessionID : historySessionID
        importSessionID = report.importSessionID
        manualPrompt = report.manualPrompt
        self.report = report
        screenState = .waitingForManualAcquisition
        architectManualDiagnostics = nil
        syncManualWorkflow(manualWorkflow.enterWaiting(
            importSessionID: report.importSessionID,
            canResume: report.canResumeManualAcquisition,
            fromHistory: true
        ))
        progress = ImportProgressSnapshot(
            phase: .waitingForManualAcquisition,
            playlistName: report.playlistName,
            totalTracks: max(report.outcomes.count, 1),
            processedTracks: report.outcomes.filter { $0.status == .added }.count,
            currentStep: report.canResumeManualAcquisition
                ? "Ajout manuel requis — reprise depuis l'historique"
                : manualAcquisitionStatus.currentStep,
            lastActivityAt: .now
        )
        if report.canResumeManualAcquisition {
            startManualPolling()
        }
    }

    func reset() {
        stopManualPolling()
        activeImportToken = nil
        screenState = .idle
        progress = ImportProgressSnapshot()
        manualPrompt = nil
        manualPollStatus = ""
        manualWorkflow.reset()
        manualAcquisitionStatus = ManualAcquisitionUIStatus()
        importSessionID = nil
        report = nil
        importedGeneration = nil
        architectErrorDetail = nil
        architectManualDiagnostics = nil
        activeHistorySessionID = ""
    }

    private func importEventHandler(for token: UUID) -> @Sendable (BridgeEventMessage) -> Void {
        { [weak self] event in
            Task { @MainActor in
                guard let self, self.activeImportToken == token else {
                    ManualContinueTrace.log(
                        "IGNORE importEventHandler stale token event=\(event.event.rawValue)"
                    )
                    return
                }
                self.handle(event: event)
            }
        }
    }

    private func beginImport(playlistName: String, totalTracks: Int, historySessionID: String = "") {
        stopManualPolling()
        activeImportToken = UUID()
        activeHistorySessionID = historySessionID
        screenState = .importing
        architectErrorDetail = nil
        architectManualDiagnostics = nil
        manualPrompt = nil
        manualPollStatus = ""
        manualWorkflow.reset()
        manualAcquisitionStatus = ManualAcquisitionUIStatus()
        importSessionID = nil
        report = nil
        progress = ImportProgressSnapshot(
            playlistName: playlistName,
            totalTracks: totalTracks,
            currentStep: "Préparation de l'import…",
            diagnostics: ["Envoi de la commande import_playlist au moteur Python…"],
            lastActivityAt: .now
        )
    }

    private func finishImport(with result: ImportResultState) {
        if result.phase == .waitingForManualAcquisition {
            screenState = .waitingForManualAcquisition
            self.report = result
            if importSessionID == nil, !result.importSessionID.isEmpty {
                importSessionID = result.importSessionID
            }
            if manualPrompt == nil, let prompt = result.manualPrompt {
                manualPrompt = prompt
            }
            syncManualWorkflow(manualWorkflow.enterWaiting(
                importSessionID: importSessionID ?? result.importSessionID,
                canResume: result.canResumeManualAcquisition,
                fromHistory: false
            ))
            mutateProgress { snapshot in
                snapshot.currentStep = manualAcquisitionStatus.currentStep
                snapshot.phase = .waitingForManualAcquisition
                snapshot.lastActivityAt = .now
            }
            startManualPolling()
            return
        }
        stopManualPolling()
        mutateProgress { snapshot in
            snapshot.addedCount = result.addedCount
            snapshot.skippedCount = result.skippedCount
            snapshot.notFoundCount = result.notFoundCount
            snapshot.errorCount = result.errorCount
            snapshot.currentStep = finalStepLabel(for: result)
            snapshot.lastActivityAt = .now
        }
        report = result
        screenState = .report
        activeImportToken = nil
    }

    private func failImport(_ error: PlaylistImportError) {
        stopManualPolling()
        architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
        screenState = .failed(ImportErrorHumanizer.message(for: error))
        activeImportToken = nil
    }

    private func failImport(_ error: Error) {
        stopManualPolling()
        architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
        screenState = .failed(ImportErrorHumanizer.userMessage(for: error))
        activeImportToken = nil
    }

    private func probeManualAcquisition() async {
        guard let importSessionID, screenState == .waitingForManualAcquisition, !isContinuingManual else { return }
        syncManualWorkflow(manualWorkflow.beginBackgroundProbe())
        mutateProgress { snapshot in
            snapshot.currentStep = manualAcquisitionStatus.currentStep
            snapshot.lastActivityAt = .now
        }

        do {
            let probe = try await service.probeManualAcquisition(importSessionID: importSessionID)
            let (snapshot, action) = manualWorkflow.applyProbeResult(probe, finishedAt: Date(), userInitiated: false)
            syncManualWorkflow(snapshot)

            if case .resumeImport(let sessionID) = action {
                ManualContinueTrace.log("CALL resumeImportAfterPositiveProbe() from background probe")
                let token = activeImportToken
                await resumeImportAfterPositiveProbe(importSessionID: sessionID, token: token)
            }
        } catch let error as PlaylistImportError {
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
            syncManualWorkflow(manualWorkflow.applyBridgeError(
                ImportErrorHumanizer.message(for: error),
                architectDetail: architectErrorDetail
            ))
        } catch {
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
            syncManualWorkflow(manualWorkflow.applyBridgeError(
                ImportErrorHumanizer.userMessage(for: error),
                architectDetail: architectErrorDetail
            ))
        }
    }

    private func syncManualWorkflow(_ snapshot: ManualAcquisitionWorkflowSnapshot) {
        manualAcquisitionStatus = snapshot.uiStatus
        manualPollStatus = snapshot.pollStatus
        architectManualDiagnostics = snapshot.architectDiagnostics
        if snapshot.isBusy || !snapshot.shouldPoll {
            stopManualPolling()
        } else if manualPollTask == nil, importSessionID != nil, screenState == .waitingForManualAcquisition {
            startManualPolling()
        }
    }

    private func handle(event: BridgeEventMessage) {
        guard acceptsImportBridgeEvents else {
            ManualContinueTrace.log(
                "IGNORE handle(event:) event=\(event.event.rawValue) screenState=\(String(describing: screenState))"
            )
            return
        }

        switch event.event {
        case .started:
            let message = startedMessage(from: event.payload)
            mutateProgress { snapshot in
                snapshot.currentStep = message
                snapshot.lastActivityAt = .now
                appendDiagnostic(message, to: &snapshot)
            }
        case .progress:
            mutateProgress { snapshot in
                if let phaseRaw = event.payload["phase"]?.stringValue,
                   let phase = ImportPhase(rawValue: phaseRaw) {
                    snapshot.phase = phase
                    snapshot.currentStep = stepLabel(for: phase)
                }
                snapshot.totalTracks = event.payload["total_tracks"]?.intValue ?? snapshot.totalTracks
                snapshot.processedTracks = event.payload["processed_tracks"]?.intValue ?? snapshot.processedTracks
                snapshot.currentTrackLabel = event.payload["current_track_label"]?.stringValue ?? snapshot.currentTrackLabel
                if let playlistName = event.payload["playlist_name"]?.stringValue, !playlistName.isEmpty {
                    snapshot.playlistName = playlistName
                }
                snapshot.addedCount = event.payload["added_count"]?.intValue ?? snapshot.addedCount
                snapshot.skippedCount = event.payload["skipped_count"]?.intValue ?? snapshot.skippedCount
                snapshot.notFoundCount = event.payload["not_found_count"]?.intValue ?? snapshot.notFoundCount
                snapshot.errorCount = event.payload["error_count"]?.intValue ?? snapshot.errorCount
                snapshot.lastActivityAt = .now
            }
            if let sessionID = event.payload["import_session_id"]?.stringValue {
                importSessionID = sessionID
            }
        case .trackProgress:
            guard let activity = parseTrackActivity(from: event.payload) else { return }
            mutateProgress { snapshot in
                applyTrackActivity(activity, to: &snapshot)
                snapshot.currentTrackLabel = activity.displayLabel
                if !activity.message.isEmpty {
                    snapshot.currentStep = activity.message
                } else {
                    snapshot.currentStep = ImportTrackActivityFormatter.stepLabel(activity.step, status: activity.status)
                }
                snapshot.addedCount = event.payload["added_count"]?.intValue ?? snapshot.addedCount
                snapshot.skippedCount = event.payload["skipped_count"]?.intValue ?? snapshot.skippedCount
                snapshot.notFoundCount = event.payload["not_found_count"]?.intValue ?? snapshot.notFoundCount
                snapshot.errorCount = event.payload["error_count"]?.intValue ?? snapshot.errorCount
                snapshot.processedTracks = max(snapshot.processedTracks, activity.trackIndex + (activity.step == .completed ? 1 : 0))
                snapshot.lastActivityAt = .now
            }
        case .diagnostic:
            guard let message = event.payload["message"]?.stringValue else { return }
            mutateProgress { snapshot in
                snapshot.currentStep = message
                if shouldSurfaceDiagnostic(message) {
                    appendDiagnostic(message, to: &snapshot)
                }
                snapshot.lastActivityAt = .now
            }
        case .error:
            guard let message = event.payload["message"]?.stringValue, !message.isEmpty else { return }
            mutateProgress { snapshot in
                snapshot.errorCount += 1
                appendDiagnostic(message, to: &snapshot, force: true)
                snapshot.lastActivityAt = .now
            }
            architectErrorDetail = message
            switch screenState {
            case .importing, .waitingForManualAcquisition:
                mutateProgress { snapshot in
                    snapshot.currentStep = ImportErrorHumanizer.humanizeBridgeMessage(message)
                }
            default:
                screenState = .failed(ImportErrorHumanizer.humanizeBridgeMessage(message))
            }
        case .manualAcquisitionRequired:
            importSessionID = event.payload["import_session_id"]?.stringValue
            manualPrompt = ManualAcquisitionPrompt(
                token: event.payload["token"]?.stringValue ?? "",
                artist: event.payload["artist"]?.stringValue ?? "",
                title: event.payload["title"]?.stringValue ?? "",
                instructions: event.payload["instructions"]?.stringValue ?? "",
                catalogLabel: event.payload["catalog_label"]?.stringValue ?? "",
                album: event.payload["album"]?.stringValue ?? "",
                catalogURL: event.payload["catalog_url"]?.stringValue ?? ""
            )
            syncManualWorkflow(manualWorkflow.enterWaiting(
                importSessionID: importSessionID ?? "",
                canResume: true,
                fromHistory: false
            ))
            mutateProgress { snapshot in
                snapshot.currentStep = "Ajout manuel requis — ouvrez Music.app via le bouton ci-dessous"
                appendDiagnostic(
                    "Acquisition manuelle requise pour \(manualPrompt?.artist ?? "") — \(manualPrompt?.title ?? "")",
                    to: &snapshot,
                    force: true
                )
                snapshot.phase = .waitingForManualAcquisition
                snapshot.lastActivityAt = .now
            }
            screenState = .waitingForManualAcquisition
            startManualPolling()
        default:
            break
        }
    }

    private func startManualPolling() {
        manualPollTask?.cancel()
        guard importSessionID != nil else { return }
        manualPollTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 4_000_000_000)
                guard let self, !Task.isCancelled else { return }
                await self.probeManualAcquisition()
            }
        }
    }

    private func stopManualPolling() {
        manualPollTask?.cancel()
        manualPollTask = nil
    }

    private func parseTrackActivity(from payload: BridgeJSONObject) -> ImportTrackActivity? {
        guard let trackKey = payload["track_key"]?.stringValue else { return nil }
        let trackIndex = payload["track_index"]?.intValue ?? 0
        return ImportTrackActivity(
            trackKey: trackKey,
            trackIndex: trackIndex,
            artist: payload["artist"]?.stringValue ?? "",
            title: payload["title"]?.stringValue ?? "",
            album: payload["album"]?.stringValue ?? "",
            section: payload["section"]?.stringValue ?? "",
            step: ImportTrackStep(rawValue: payload["step"]?.stringValue ?? "") ?? .pending,
            status: ImportTrackStatus(rawValue: payload["status"]?.stringValue ?? "") ?? .pending,
            message: payload["message"]?.stringValue ?? "",
            catalogURL: payload["catalog_url"]?.stringValue ?? "",
            isCurrent: payload["is_current"]?.boolValue ?? true
        )
    }

    private func applyTrackActivity(_ activity: ImportTrackActivity, to snapshot: inout ImportProgressSnapshot) {
        var activities = snapshot.activities.map { item in
            var updated = item
            updated.isCurrent = false
            return updated
        }
        if let index = activities.firstIndex(where: { $0.trackKey == activity.trackKey }) {
            activities[index] = activity
        } else {
            activities.append(activity)
        }
        if activities.count > ImportProgressSnapshot.maxVisibleActivities {
            activities.removeFirst(activities.count - ImportProgressSnapshot.maxVisibleActivities)
        }
        snapshot.activities = activities
    }

    private func mutateProgress(_ block: (inout ImportProgressSnapshot) -> Void) {
        var snapshot = progress
        block(&snapshot)
        progress = snapshot
    }

    private func appendDiagnostic(
        _ message: String,
        to snapshot: inout ImportProgressSnapshot,
        force: Bool = false
    ) {
        guard !message.isEmpty else { return }
        if !force, snapshot.diagnostics.last == message {
            return
        }
        if snapshot.diagnostics.count >= ImportProgressSnapshot.maxVisibleDiagnostics {
            snapshot.diagnostics.removeFirst(
                snapshot.diagnostics.count - ImportProgressSnapshot.maxVisibleDiagnostics + 1
            )
        }
        snapshot.diagnostics.append(message)
    }

    private func shouldSurfaceDiagnostic(_ message: String) -> Bool {
        let lowered = message.lowercased()
        if message.hasPrefix("[stderr]") || message.hasPrefix("[bridge error]") {
            return lowered.contains("failed")
                || lowered.contains("error")
                || lowered.contains("échec")
                || lowered.contains("introuvable")
        }
        return lowered.contains("music.app")
            || lowered.contains("résolution")
            || lowered.contains("resolve")
            || lowered.contains("synchronis")
            || lowered.contains("création")
            || lowered.contains("commande")
            || lowered.contains("livraison")
            || lowered.contains("deliver")
            || lowered.contains("introuvable")
            || lowered.contains("cache")
            || lowered.contains(" ms")
            || lowered.contains("lot ")
            || lowered.contains("[+")
    }

    private func startedMessage(from payload: BridgeJSONObject) -> String {
        if let message = payload["message"]?.stringValue, !message.isEmpty {
            return message
        }
        if let command = payload["command"]?.stringValue, !command.isEmpty {
            return "Commande bridge envoyée : \(command)"
        }
        return "Import démarré"
    }

    private func stepLabel(for phase: ImportPhase) -> String {
        switch phase {
        case .resolving: return "Résolution des morceaux dans Apple Music…"
        case .acquiring: return "Acquisition catalogue…"
        case .delivering: return "Synchronisation avec Music.app…"
        case .waitingForManualAcquisition: return "En attente d'ajout manuel"
        default: return "Import en cours…"
        }
    }

    private func finalStepLabel(for result: ImportResultState) -> String {
        switch result.phase {
        case .completed:
            return "Playlist créée — \(result.addedCount) morceau(x) ajouté(s)"
        case .partialSuccess:
            return "Import partiel — \(result.addedCount) ajouté(s), \(result.notFoundCount) introuvable(s), \(result.skippedCount) ignoré(s)"
        case .failed:
            return "Import échoué"
        default:
            return "Import terminé"
        }
    }

    private func flushPendingImportEvents() async {
        for _ in 0..<8 {
            await Task.yield()
        }
    }

    private var acceptsImportBridgeEvents: Bool {
        switch screenState {
        case .importing, .waitingForManualAcquisition:
            return activeImportToken != nil
        case .idle, .report, .failed:
            return false
        }
    }
}
