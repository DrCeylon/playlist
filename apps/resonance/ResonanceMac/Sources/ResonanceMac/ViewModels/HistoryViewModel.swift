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
    @Published var playlistPreview: PlaylistGenerationResult?

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

    var viewActionDescription: String {
        "Affiche la liste complète des morceaux générés pour cette session."
    }

    var editActionDescription: String {
        "Recharge le formulaire Nouvelle Playlist avec la demande enregistrée."
    }

    var importActionDescription: String {
        "Recrée la playlist dans Apple Music à partir de la preview enregistrée."
    }

    var retryActionDescription: String {
        "Relance la génération avec les mêmes paramètres enregistrés."
    }

    var exportActionDescription: String {
        "Ouvre le rapport technique de la session dans le Finder (mode diagnostic)."
    }

    var canViewSelectedPlaylist: Bool {
        guard let detail = selectedDetail else { return false }
        return !detail.generationResult.isEmpty
    }

    var canEditSelectedPlaylist: Bool {
        guard let detail = selectedDetail else { return false }
        return HistoryPayloadMapper.generationRequest(from: detail.generationRequest) != nil
    }

    var canImportSelectedSession: Bool {
        guard let detail = selectedDetail else { return false }
        return !detail.generationResult.isEmpty
    }

    var canRetrySelectedSession: Bool {
        guard let detail = selectedDetail else { return false }
        return !detail.generationRequest.isEmpty
    }

    var viewDisabledReason: String? {
        guard selectedDetail != nil else { return "Sélectionne une session." }
        if canViewSelectedPlaylist { return nil }
        return "Aucune preview enregistrée pour cette session."
    }

    var editDisabledReason: String? {
        guard selectedDetail != nil else { return "Sélectionne une session." }
        if canEditSelectedPlaylist { return nil }
        return "Demande originale indisponible pour cette session."
    }

    var importDisabledReason: String? {
        guard selectedDetail != nil else { return "Sélectionne une session." }
        if canImportSelectedSession { return nil }
        return "Preview indisponible — import impossible."
    }

    var retryDisabledReason: String? {
        guard selectedDetail != nil else { return "Sélectionne une session." }
        if canRetrySelectedSession { return nil }
        return "Paramètres de génération indisponibles."
    }

    func editRequestForSelectedSession() -> PlaylistGenerationRequest? {
        guard let detail = selectedDetail else { return nil }
        return HistoryPayloadMapper.generationRequest(from: detail.generationRequest)
    }

    func preparePlaylistPreview() {
        guard let detail = selectedDetail else {
            actionFeedback = .failure("Sélectionne une session avant d'afficher la playlist.")
            return
        }
        guard canViewSelectedPlaylist else {
            actionFeedback = .failure(viewDisabledReason ?? "Preview indisponible.")
            return
        }
        do {
            playlistPreview = try HistoryPayloadMapper.generationResult(from: detail.generationResult)
        } catch {
            playlistPreview = nil
            actionFeedback = .failure("Impossible d'afficher la playlist enregistrée.")
        }
    }

    func dismissPlaylistPreview() {
        playlistPreview = nil
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
        playlistPreview = nil
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
                    playlistPreview = nil
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
                playlistPreview = nil
                actionFeedback = .success("Historique vidé.")
            } else {
                actionFeedback = .failure("Nettoyage impossible.")
            }
        } catch {
            actionFeedback = .failure("Nettoyage impossible.")
        }
    }

    func retryGeneration() async {
        guard !isBusy else { return }
        guard let sessionID = selectedDetail?.summary.sessionID else {
            actionFeedback = .failure("Sélectionne une session avant de réessayer.")
            return
        }
        guard canRetrySelectedSession else {
            actionFeedback = .failure(retryDisabledReason ?? "Paramètres indisponibles.")
            return
        }

        actionFeedback = .inProgress("Génération en cours…")
        do {
            let result = try await service.replayGeneration(sessionID: sessionID)
            actionFeedback = .success(
                "Playlist régénérée — «\(result.playlistName)» (\(result.trackCount) morceau(x))."
            )
        } catch let error as SessionHistoryServiceError {
            actionFeedback = .failure("Réessai impossible : \(message(for: error))")
        } catch {
            actionFeedback = .failure("Réessai impossible : erreur inattendue.")
        }
    }

    func importSelected() async {
        guard !isBusy else { return }
        guard let detail = selectedDetail else {
            actionFeedback = .failure("Sélectionne une session avant d'importer.")
            return
        }
        guard canImportSelectedSession else {
            actionFeedback = .failure(importDisabledReason ?? "Données insuffisantes pour importer.")
            return
        }

        actionFeedback = .inProgress("Import Apple Music en cours…")
        do {
            let generation = try HistoryPayloadMapper.generationResult(from: detail.generationResult)
            let importResult = try await importService.importPlaylist(generation) { [weak self] event in
                Task { @MainActor in
                    self?.handleImportEvent(event)
                }
            }
            if importResult.phase == .waitingForManualAcquisition {
                actionFeedback = .failure(
                    "Import interrompu : ajout manuel requis dans Music.app. Utilise Nouvelle Playlist pour terminer."
                )
                return
            }
            actionFeedback = .success(
                "Import terminé — \(importResult.addedCount) ajouté(s), \(importResult.skippedCount) ignoré(s)."
            )
            await refresh()
            await select(session: detail.summary)
        } catch let error as PlaylistImportError {
            actionFeedback = .failure(ImportErrorHumanizer.message(for: error))
        } catch {
            actionFeedback = .failure(ImportErrorHumanizer.userMessage(for: error))
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
                actionFeedback = .success("Rapport ouvert : \(opened.path)")
                return
            }

            actionFeedback = .success(
                "Export JSON prêt (session \(export.sessionID)). Aucun fichier rapport sur disque."
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
                actionFeedback = .inProgress("Import Apple Music — \(processed)/\(total) morceaux")
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
            return ImportErrorHumanizer.humanizeBridgeMessage(payload.message)
        }
    }
}
