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
    @Published private(set) var isContinuingManual = false

    private let service: any PlaylistImportServing
    private var importSessionID: String?
    private var manualPollTask: Task<Void, Never>?
    private var importedGeneration: PlaylistGenerationResult?
    private var activeImportToken: UUID?

    init(service: any PlaylistImportServing = MockPlaylistImportService()) {
        self.service = service
    }

    func importPlaylist(_ generationResult: PlaylistGenerationResult) async {
        importedGeneration = generationResult
        beginImport(
            playlistName: generationResult.playlistName,
            totalTracks: generationResult.trackCount,
            historySessionID: generationResult.historySessionID
        )

        do {
            let result = try await service.importPlaylist(generationResult, onEvent: importEventHandler)
            await flushPendingImportEvents()
            finishImport(with: result)
        } catch let error as PlaylistImportError {
            failImport(error)
        } catch {
            failImport(error)
        }
    }

    func retryImportTrack(at index: Int) async {
        guard let importedGeneration else {
            screenState = .failed("Impossible de réessayer : playlist source introuvable.")
            return
        }
        beginImport(
            playlistName: importedGeneration.playlistName,
            totalTracks: 1,
            historySessionID: importedGeneration.historySessionID
        )
        mutateProgress { snapshot in
            snapshot.currentStep = "Nouvelle tentative pour un morceau…"
            snapshot.totalTracks = importedGeneration.trackCount
        }
        screenState = .importing

        do {
            let result = try await service.retryImportTracks(
                importedGeneration,
                trackIndices: [index],
                onEvent: importEventHandler
            )
            await flushPendingImportEvents()
            finishImport(with: result)
        } catch let error as PlaylistImportError {
            failImport(error)
        } catch {
            failImport(error)
        }
    }

    func confirmManualAcquisition() async {
        guard !isContinuingManual else { return }
        isContinuingManual = true
        defer { isContinuingManual = false }

        stopManualPolling()
        guard let importSessionID else {
            screenState = .failed("Session d'import introuvable.")
            updateManualStatus(
                currentStep: "Session d'import introuvable",
                lastVerificationResult: "Session d'import introuvable.",
                userAdvice: "Relancez l'import depuis l'historique ou Nouvelle Playlist."
            )
            return
        }
        let token = activeImportToken
        let clickTime = Date()
        architectManualDiagnostics = nil
        updateManualStatus(
            lastUserClickAt: clickTime,
            currentStep: "Recherche dans la bibliothèque Music.app…",
            lastVerificationResult: "",
            userAdvice: "Vérification en cours — patientez quelques secondes.",
            backendMessage: nil,
            backendErrorCode: nil
        )
        manualPollStatus = "Vérification lancée à \(ManualAcquisitionUIStatus.formattedClickTime(clickTime)) — recherche dans Music.app…"
        mutateProgress { snapshot in
            snapshot.currentStep = "Recherche dans la bibliothèque Music.app…"
            snapshot.lastActivityAt = .now
        }
        await Task.yield()

        do {
            let probeStartedAt = Date()
            updateManualStatus(lastProbeStartedAt: probeStartedAt)
            let probe = try await service.probeManualAcquisition(importSessionID: importSessionID)
            let probeFinishedAt = Date()
            applyProbeDiagnostics(probe, finishedAt: probeFinishedAt)
            guard token == nil || token == activeImportToken else { return }

            if probe.errorCode == "checkpoint_missing" {
                updateManualStatus(
                    currentStep: "Session expirée",
                    lastVerificationResult: probe.message,
                    userAdvice: "Relancez l'import depuis l'aperçu ou l'historique.",
                    backendMessage: probe.message,
                    backendErrorCode: probe.errorCode
                )
                manualPollStatus = probe.message
                screenState = .waitingForManualAcquisition
                return
            }

            if let probeError = probe.diagnostics?.probeError, !probeError.isEmpty {
                updateManualStatus(
                    currentStep: "Erreur technique",
                    lastVerificationResult: probe.message,
                    userAdvice: "Vérifiez Music.app et les autorisations Automatisation, puis réessayez.",
                    backendMessage: probe.message,
                    backendErrorCode: probe.errorCode ?? "probe_error"
                )
                manualPollStatus = probe.message
                screenState = .waitingForManualAcquisition
                startManualPolling()
                return
            }

            if !probe.found {
                let message = probe.message.isEmpty
                    ? "Morceau pas encore détecté dans la bibliothèque. Vérifiez qu'il a bien été ajouté dans Music.app, puis réessayez."
                    : probe.message
                updateManualStatus(
                    currentStep: "Morceau non détecté",
                    lastVerificationResult: message,
                    userAdvice: "Ajoutez le morceau dans Music.app, puis cliquez à nouveau sur continuer.",
                    backendMessage: message,
                    backendErrorCode: probe.errorCode ?? "track_not_found"
                )
                manualPollStatus = message
                screenState = .waitingForManualAcquisition
                startManualPolling()
                return
            }

            let detectedMessage = probe.message.isEmpty
                ? "Morceau détecté, reprise de l'import…"
                : probe.message
            updateManualStatus(
                currentStep: "Morceau détecté — reprise de l'import…",
                lastVerificationResult: detectedMessage,
                userAdvice: "Import en cours — suivez la progression ci-dessus.",
                backendMessage: detectedMessage,
                backendErrorCode: nil
            )
            screenState = .importing
            manualPollStatus = detectedMessage
            mutateProgress { snapshot in
                snapshot.currentStep = "Reprise après ajout manuel…"
                snapshot.lastActivityAt = .now
            }

            let result = try await service.continueManualAcquisition(
                importSessionID: importSessionID,
                onEvent: importEventHandler
            )
            await flushPendingImportEvents()
            guard token == nil || token == activeImportToken else { return }
            if result.phase == .waitingForManualAcquisition {
                let message = "Morceau pas encore détecté dans la bibliothèque. Vérifiez qu'il a bien été ajouté dans Music.app, puis réessayez."
                updateManualStatus(
                    currentStep: "Morceau non détecté",
                    lastVerificationResult: message,
                    userAdvice: "Ajoutez le morceau dans Music.app, puis réessayez.",
                    backendMessage: message,
                    backendErrorCode: "track_not_found"
                )
                manualPollStatus = message
            }
            finishImport(with: result)
        } catch let error as PlaylistImportError {
            guard token == nil || token == activeImportToken else { return }
            let message = ImportErrorHumanizer.message(for: error)
            updateManualStatus(
                currentStep: "Erreur technique",
                lastVerificationResult: message,
                userAdvice: "Corrigez le problème indiqué puis réessayez.",
                backendMessage: message,
                backendErrorCode: "bridge_error"
            )
            manualPollStatus = message
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
            screenState = .waitingForManualAcquisition
            startManualPolling()
        } catch {
            guard token == nil || token == activeImportToken else { return }
            let message = ImportErrorHumanizer.userMessage(for: error)
            updateManualStatus(
                currentStep: "Erreur technique",
                lastVerificationResult: message,
                userAdvice: "Corrigez le problème indiqué puis réessayez.",
                backendMessage: message,
                backendErrorCode: "bridge_error"
            )
            manualPollStatus = message
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
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
        manualAcquisitionStatus = ManualAcquisitionUIStatus(
            currentStep: "En attente d'ajout manuel",
            lastVerificationResult: "",
            userAdvice: report.canResumeManualAcquisition
                ? "Ajoutez le morceau dans Music.app, puis cliquez sur continuer."
                : "Relancez l'import depuis l'aperçu."
        )
        manualPollStatus = report.canResumeManualAcquisition
            ? "Reprise depuis l'historique — ajoutez le morceau dans Music.app si nécessaire."
            : "La session d'import a expiré. Relancez l'import depuis l'aperçu."
        progress = ImportProgressSnapshot(
            playlistName: report.playlistName,
            totalTracks: max(report.outcomes.count, 1),
            processedTracks: report.outcomes.filter { $0.status == .added }.count,
            currentStep: "Ajout manuel requis — reprise depuis l'historique",
            phase: .waitingForManualAcquisition,
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
        manualAcquisitionStatus = ManualAcquisitionUIStatus()
        importSessionID = nil
        report = nil
        importedGeneration = nil
        architectErrorDetail = nil
        architectManualDiagnostics = nil
        activeHistorySessionID = ""
    }

    private var importEventHandler: @Sendable (BridgeEventMessage) -> Void {
        { [weak self] event in
            Task { @MainActor in
                self?.handle(event: event)
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
    }

    private func failImport(_ error: PlaylistImportError) {
        stopManualPolling()
        architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
        screenState = .failed(ImportErrorHumanizer.message(for: error))
    }

    private func failImport(_ error: Error) {
        stopManualPolling()
        architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
        screenState = .failed(ImportErrorHumanizer.userMessage(for: error))
    }

    private func updateManualStatus(
        lastUserClickAt: Date? = nil,
        currentStep: String? = nil,
        lastVerificationResult: String? = nil,
        userAdvice: String? = nil,
        lastProbeStartedAt: Date? = nil,
        lastProbeFinishedAt: Date? = nil,
        lastProbeDurationMs: Int? = nil,
        backendMessage: String? = nil,
        backendErrorCode: String? = nil
    ) {
        var status = manualAcquisitionStatus
        if let lastUserClickAt { status.lastUserClickAt = lastUserClickAt }
        if let currentStep { status.currentStep = currentStep }
        if let lastVerificationResult { status.lastVerificationResult = lastVerificationResult }
        if let userAdvice { status.userAdvice = userAdvice }
        if let lastProbeStartedAt { status.lastProbeStartedAt = lastProbeStartedAt }
        if let lastProbeFinishedAt { status.lastProbeFinishedAt = lastProbeFinishedAt }
        if let lastProbeDurationMs { status.lastProbeDurationMs = lastProbeDurationMs }
        if let backendMessage { status.backendMessage = backendMessage }
        if let backendErrorCode { status.backendErrorCode = backendErrorCode }
        manualAcquisitionStatus = status
    }

    private func applyProbeDiagnostics(_ probe: ManualAcquisitionProbeResult, finishedAt: Date) {
        let startedAt = probe.diagnostics?.probeStartedAt ?? manualAcquisitionStatus.lastProbeStartedAt ?? finishedAt
        let durationMs = probe.diagnostics?.probeDurationMs
            ?? Int(finishedAt.timeIntervalSince(startedAt) * 1000)
        updateManualStatus(
            lastProbeFinishedAt: probe.diagnostics?.probeFinishedAt ?? finishedAt,
            lastProbeDurationMs: durationMs,
            backendMessage: probe.message,
            backendErrorCode: probe.errorCode
        )

        var architectLines: [String] = []
        if let errorCode = probe.errorCode, !errorCode.isEmpty {
            architectLines.append("backend_error_code: \(errorCode)")
        }
        if !probe.message.isEmpty {
            architectLines.append("backend_message: \(probe.message)")
        }
        if let summary = probe.architectSummary {
            architectLines.append(summary)
        }
        if let sessionID = probe.diagnostics?.importSessionID, !sessionID.isEmpty {
            architectLines.append("import_session_id: \(sessionID)")
        }
        architectManualDiagnostics = architectLines.isEmpty ? nil : architectLines.joined(separator: "\n")
    }

    private func handle(event: BridgeEventMessage) {
        guard activeImportToken != nil || screenState != .idle else { return }

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
            mutateProgress { snapshot in
                snapshot.currentStep = "Ajout manuel requis — ouvrez Music.app via le bouton ci-dessous"
                appendDiagnostic(
                    "Acquisition manuelle requise pour \(manualPrompt?.artist ?? "") — \(manualPrompt?.title ?? "")",
                    to: &snapshot,
                    force: true
                )
                snapshot.lastActivityAt = .now
            }
            screenState = .waitingForManualAcquisition
            manualAcquisitionStatus = ManualAcquisitionUIStatus(
                currentStep: "En attente d'ajout manuel",
                lastVerificationResult: "",
                userAdvice: "Ajoutez le morceau dans Music.app, puis cliquez sur continuer."
            )
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

    private func probeManualAcquisition() async {
        guard let importSessionID, screenState == .waitingForManualAcquisition, !isContinuingManual else { return }
        do {
            let probeStartedAt = Date()
            updateManualStatus(
                currentStep: "Vérification automatique de la bibliothèque…",
                lastProbeStartedAt: probeStartedAt
            )
            let probe = try await service.probeManualAcquisition(importSessionID: importSessionID)
            applyProbeDiagnostics(probe, finishedAt: Date())

            if probe.errorCode == "checkpoint_missing" {
                updateManualStatus(
                    currentStep: "Session expirée",
                    lastVerificationResult: probe.message,
                    userAdvice: "Relancez l'import depuis l'aperçu."
                )
                manualPollStatus = probe.message
                stopManualPolling()
                return
            }

            if let probeError = probe.diagnostics?.probeError, !probeError.isEmpty {
                updateManualStatus(
                    currentStep: "Erreur technique",
                    lastVerificationResult: probe.message,
                    userAdvice: "Utilisez le bouton continuer pour relancer la vérification."
                )
                manualPollStatus = probe.message
                return
            }

            if probe.found {
                let message = probe.message.isEmpty
                    ? "Morceau détecté — reprise automatique…"
                    : probe.message
                updateManualStatus(
                    currentStep: "Morceau détecté — reprise automatique…",
                    lastVerificationResult: message,
                    userAdvice: "Reprise de l'import en cours."
                )
                manualPollStatus = message
                await confirmManualAcquisition()
            } else {
                let message = probe.message.isEmpty
                    ? "En attente de détection dans Music.app…"
                    : probe.message
                updateManualStatus(
                    currentStep: "Morceau non détecté",
                    lastVerificationResult: message,
                    userAdvice: "Ajoutez le morceau dans Music.app, puis cliquez sur continuer."
                )
                manualPollStatus = message
            }
        } catch let error as PlaylistImportError {
            let message = ImportErrorHumanizer.message(for: error)
            updateManualStatus(
                currentStep: "Erreur technique",
                lastVerificationResult: message,
                userAdvice: "Utilisez le bouton continuer pour relancer la vérification."
            )
            manualPollStatus = message
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
        } catch {
            let message = ImportErrorHumanizer.userMessage(for: error)
            updateManualStatus(
                currentStep: "Erreur technique",
                lastVerificationResult: message,
                userAdvice: "Utilisez le bouton continuer pour relancer la vérification."
            )
            manualPollStatus = message
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
        }
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
}
