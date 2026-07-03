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

    private let service: any SessionHistoryServing
    private let importService: any PlaylistImportServing

    init(
        service: any SessionHistoryServing = PythonEngineBridgeService(),
        importService: any PlaylistImportServing = PythonEngineBridgeService()
    ) {
        self.service = service
        self.importService = importService
    }

    var isBusy: Bool {
        if case .inProgress = actionFeedback { return true }
        return screenState == .loading
    }

    var replayActionDescription: String {
        "Relance la génération Python avec la requête enregistrée pour cette session."
    }

    var reimportActionDescription: String {
        "Recrée la playlist dans Apple Music à partir de l'aperçu enregistré (mêmes morceaux/sections)."
    }

    var exportActionDescription: String {
        "Ouvre le rapport JSON ou texte de la session dans le Finder, s'il existe sur disque."
    }

    var canReplaySelectedSession: Bool {
        guard let detail = selectedDetail else { return false }
        return !detail.generationRequest.isEmpty
    }

    var canReimportSelectedSession: Bool {
        guard let detail = selectedDetail else { return false }
        return !detail.generationResult.isEmpty
    }

    var replayDisabledReason: String? {
        guard selectedDetail != nil else { return "Sélectionne une session." }
        if canReplaySelectedSession { return nil }
        return "Requête indisponible pour cette session."
    }

    var reimportDisabledReason: String? {
        guard selectedDetail != nil else { return "Sélectionne une session." }
        if canReimportSelectedSession { return nil }
        return "Aperçu indisponible — réimport impossible pour cette session."
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

    func delete(session: SessionHistorySummary) async {
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

    func clearAll() async {
        guard !isBusy else { return }
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

    func replayGeneration() async {
        guard !isBusy else { return }
        guard let sessionID = selectedDetail?.summary.sessionID else {
            actionFeedback = .failure("Sélectionne une session avant de relancer.")
            return
        }
        guard canReplaySelectedSession else {
            actionFeedback = .failure(replayDisabledReason ?? "Requête indisponible pour cette session.")
            return
        }

        actionFeedback = .inProgress("Relance de la génération en cours…")
        do {
            let result = try await service.replayGeneration(sessionID: sessionID)
            actionFeedback = .success(
                "Relance OK — «\(result.playlistName)» (\(result.trackCount) morceau(x), score moyen \(String(format: "%.2f", result.averageScore)))."
            )
        } catch let error as SessionHistoryServiceError {
            actionFeedback = .failure("Relance impossible : \(message(for: error))")
        } catch {
            actionFeedback = .failure("Relance impossible : erreur inattendue.")
        }
    }

    func reimportSelected() async {
        guard !isBusy else { return }
        guard let detail = selectedDetail else {
            actionFeedback = .failure("Sélectionne une session avant de réimporter.")
            return
        }
        guard canReimportSelectedSession else {
            actionFeedback = .failure(reimportDisabledReason ?? "Données insuffisantes pour réimporter.")
            return
        }

        actionFeedback = .inProgress("Réimport Apple Music en cours…")
        do {
            let generation = try HistoryPayloadMapper.generationResult(from: detail.generationResult)
            let importResult = try await importService.importPlaylist(generation) { [weak self] event in
                Task { @MainActor in
                    self?.handleImportEvent(event)
                }
            }
            if importResult.phase == .waitingForManualAcquisition {
                actionFeedback = .failure(
                    "Réimport interrompu : ajout manuel requis dans Music.app. Utilise Nouvelle Playlist pour terminer l'import interactif."
                )
                return
            }
            actionFeedback = .success(
                "Réimport terminé — ajoutés \(importResult.addedCount), ignorés \(importResult.skippedCount), introuvables \(importResult.notFoundCount), erreurs \(importResult.errorCount)."
            )
            await refresh()
            await select(session: detail.summary)
        } catch let error as PlaylistImportError {
            actionFeedback = .failure("Réimport impossible : \(ImportErrorHumanizer.message(for: error))")
        } catch {
            actionFeedback = .failure("Réimport impossible : \(ImportErrorHumanizer.userMessage(for: error))")
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
