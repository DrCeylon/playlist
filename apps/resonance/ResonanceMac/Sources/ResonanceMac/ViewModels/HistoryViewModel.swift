import AppKit
import Foundation
import ResonanceCore

@MainActor
final class HistoryViewModel: ObservableObject {
    enum ScreenState: Equatable {
        case idle
        case loading
        case ready
        case failed(String)
    }

    enum ActionFeedback: Equatable {
        case none
        case inProgress(String)
        case success(String)
        case failure(String)
    }

    @Published var screenState: ScreenState = .idle
    @Published var sessions: [SessionHistorySummary] = []
    @Published var selectedDetail: SessionHistoryDetail?
    @Published var actionFeedback: ActionFeedback = .none
    @Published var architectErrorDetail: String?

    private var service: any SessionHistoryServing
    private var importService: any PlaylistImportServing

    init(
        service: any SessionHistoryServing = PythonEngineBridgeService(),
        importService: any PlaylistImportServing = PythonEngineBridgeService()
    ) {
        self.service = service
        self.importService = importService
    }

    func replaceServices(
        historyService: any SessionHistoryServing,
        importService: any PlaylistImportServing
    ) {
        self.service = historyService
        self.importService = importService
    }

    var isBusy: Bool {
        if case .inProgress = actionFeedback { return true }
        return screenState == .loading
    }

    var resumeContent: HistoryWorkflowResumeView.ResumeContent {
        guard let detail = selectedDetail else { return .none }

        switch detail.summary.status {
        case .imported, .partialSuccess:
            if let report = importReport(from: detail) {
                return .importReport(report)
            }
        case .waitingForManualAcquisition:
            if let report = importReport(from: detail) {
                if report.canResumeManualAcquisition {
                    return .manualAcquisitionWaiting(report)
                }
                return .manualAcquisitionUnavailable(
                    report,
                    hasRequest: editRequestForSelectedSession() != nil,
                    playlistName: detail.summary.playlistName
                )
            }
        case .generated:
            if let preview = previewResult(from: detail) {
                return .preview(preview)
            }
        case .failed:
            if let report = importReport(from: detail) {
                return .importReport(report)
            }
            if let preview = previewResult(from: detail) {
                return .preview(preview)
            }
        }

        let hasRequest = editRequestForSelectedSession() != nil
        return .unavailable(
            hasRequest: hasRequest,
            playlistName: detail.summary.playlistName
        )
    }

    func editRequestForSelectedSession() -> PlaylistGenerationRequest? {
        guard let detail = selectedDetail else { return nil }
        return HistoryPayloadMapper.generationRequest(from: detail.generationRequest)
    }

    func generationResultForSelectedSession() -> PlaylistGenerationResult? {
        guard let detail = selectedDetail else { return nil }
        return previewResult(from: detail)
    }

    func importReportForSelectedSession() -> ImportResultState? {
        guard let detail = selectedDetail else { return nil }
        return importReport(from: detail)
    }

    func refresh() async {
        guard !isBusy else { return }
        screenState = .loading
        architectErrorDetail = nil
        do {
            sessions = try await service.listHistory()
            screenState = .ready
        } catch let error as SessionHistoryServiceError {
            screenState = .failed(message(for: error))
            if case .invalidResponse = error {
                architectErrorDetail = "Réponse bridge sans liste sessions valide."
            } else if case .bridge(let payload) = error {
                architectErrorDetail = "\(payload.code.rawValue): \(payload.message)"
            }
        } catch {
            screenState = .failed("Impossible de charger l'historique.")
            architectErrorDetail = String(describing: error)
        }
    }

    func select(session: SessionHistorySummary) async {
        actionFeedback = .none
        do {
            selectedDetail = try await service.getHistorySession(sessionID: session.sessionID)
        } catch let error as SessionHistoryServiceError {
            actionFeedback = .failure("Détail indisponible : \(message(for: error))")
        } catch {
            actionFeedback = .failure("Détail indisponible.")
        }
    }

    func delete(session: SessionHistorySummary, isProtected: (SessionHistorySummary) -> Bool = { _ in false }) async {
        if isProtected(session) {
            actionFeedback = .failure("Impossible de supprimer la session en cours — processus actif.")
            return
        }
        do {
            let deleted = try await service.deleteHistorySession(sessionID: session.sessionID)
            if deleted {
                sessions.removeAll { $0.sessionID == session.sessionID }
                if selectedDetail?.summary.sessionID == session.sessionID {
                    selectedDetail = nil
                }
                actionFeedback = .success("Session supprimée.")
            } else {
                actionFeedback = .failure("Suppression locale impossible.")
            }
        } catch {
            actionFeedback = .failure("Suppression locale impossible.")
        }
    }

    func clearAll(preservingSessionID: String? = nil) async {
        guard !isBusy else { return }

        let preservedID = preservingSessionID?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        if !preservedID.isEmpty {
            let deletable = sessions.filter { $0.sessionID != preservedID }
            guard !deletable.isEmpty else {
                actionFeedback = .failure("Aucune autre session à supprimer — la session active est conservée.")
                return
            }

            do {
                for session in deletable {
                    _ = try await service.deleteHistorySession(sessionID: session.sessionID)
                }
                sessions = sessions.filter { $0.sessionID == preservedID }
                if selectedDetail?.summary.sessionID != preservedID {
                    selectedDetail = nil
                }
                actionFeedback = .success(
                    "Historique partiellement vidé — la session active «\(sessions.first?.playlistName ?? preservedID)» est conservée."
                )
            } catch {
                actionFeedback = .failure("Nettoyage partiel impossible.")
            }
            return
        }

        do {
            let cleared = try await service.clearHistory()
            if cleared {
                sessions = []
                selectedDetail = nil
                actionFeedback = .success("Historique vidé.")
            } else {
                actionFeedback = .failure("Nettoyage impossible.")
            }
        } catch {
            actionFeedback = .failure("Nettoyage impossible.")
        }
    }

    func retryImportTrack(at index: Int) async {
        guard !isBusy else { return }
        guard let detail = selectedDetail else {
            actionFeedback = .failure("Sélectionne une session avant de réessayer.")
            return
        }
        guard let generation = previewResult(from: detail) else {
            actionFeedback = .failure("Aperçu indisponible — réessai impossible pour cette session.")
            return
        }

        actionFeedback = .inProgress("Nouvelle tentative d'import…")
        do {
            let importResult = try await importService.retryImportTracks(
                generation,
                trackIndices: [index],
                existingOutcomes: importReport(from: detail)?.outcomes,
                historySessionID: detail.summary.sessionID,
                onEvent: { [weak self] event in
                    Task { @MainActor in
                        self?.handleImportEvent(event)
                    }
                }
            )
            actionFeedback = .success(
                "Réessai terminé — ajoutés \(importResult.addedCount), introuvables \(importResult.notFoundCount), erreurs \(importResult.errorCount)."
            )
            let sessionID = detail.summary.sessionID
            await refresh()
            if let refreshed = sessions.first(where: { $0.sessionID == sessionID }) {
                await select(session: refreshed)
            } else {
                await select(session: detail.summary)
            }
        } catch let error as PlaylistImportError {
            actionFeedback = .failure("Réessai impossible : \(ImportErrorHumanizer.message(for: error))")
        } catch {
            actionFeedback = .failure("Réessai impossible : \(ImportErrorHumanizer.userMessage(for: error))")
        }
    }

    func exportSelection() async {
        guard !isBusy else { return }
        guard let sessionID = selectedDetail?.summary.sessionID else {
            actionFeedback = .failure("Sélectionne une session avant d'exporter.")
            return
        }

        actionFeedback = .inProgress("Export de la session…")
        do {
            guard let export = try await service.exportHistorySession(sessionID: sessionID) else {
                actionFeedback = .failure("Export indisponible pour cette session.")
                return
            }

            if let opened = openExportedFile(export.jsonReportPath) ?? openExportedFile(export.textReportPath) {
                actionFeedback = .success("Export ouvert : \(opened.path)")
                return
            }

            actionFeedback = .success(
                "Export JSON prêt (session \(export.sessionID), statut \(export.status.rawValue)). Aucun fichier rapport sur disque — données disponibles via le bridge."
            )
        } catch let error as SessionHistoryServiceError {
            actionFeedback = .failure("Export impossible : \(message(for: error))")
        } catch {
            actionFeedback = .failure("Export impossible : fichier introuvable ou erreur inattendue.")
        }
    }

    private func previewResult(from detail: SessionHistoryDetail) -> PlaylistGenerationResult? {
        guard !detail.generationResult.isEmpty else { return nil }
        return try? HistoryPayloadMapper.generationResult(from: detail.generationResult)
    }

    private func importReport(from detail: SessionHistoryDetail) -> ImportResultState? {
        guard !detail.importResult.isEmpty else { return nil }
        return try? HistoryPayloadMapper.importResult(from: detail.importResult)
    }

    private func handleImportEvent(_ event: BridgeEventMessage) {
        switch event.event {
        case .diagnostic:
            if let message = event.payload["message"]?.stringValue {
                actionFeedback = .inProgress(message)
            }
        case .progress:
            if let processed = event.payload["processed_tracks"]?.intValue,
               let total = event.payload["total_tracks"]?.intValue,
               total > 0 {
                actionFeedback = .inProgress("Réimport Apple Music — \(processed)/\(total) morceaux")
            }
        default:
            break
        }
    }

    private func openExportedFile(_ path: String) -> URL? {
        let trimmed = path.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }

        let url: URL
        if trimmed.hasPrefix("/") {
            url = URL(fileURLWithPath: trimmed)
        } else if let repo = ResonancePaths.repoRoot() {
            url = repo.appendingPathComponent(trimmed)
        } else {
            url = URL(fileURLWithPath: trimmed)
        }

        guard FileManager.default.fileExists(atPath: url.path) else { return nil }
        NSWorkspace.shared.activateFileViewerSelecting([url])
        return url
    }

    private func message(for error: SessionHistoryServiceError) -> String {
        switch error {
        case .bridgeUnavailable:
            return "Moteur Python introuvable. Lance l'app depuis apps/resonance ou définis RESONANCE_REPO_ROOT."
        case .timeout:
            return "Le moteur Python n'a pas répondu à temps."
        case .invalidResponse:
            return "Réponse bridge invalide pour l'historique."
        case .bridge(let payload):
            return payload.message
        }
    }
}
