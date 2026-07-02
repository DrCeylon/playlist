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

    @Published var screenState: ScreenState = .idle
    @Published var sessions: [SessionHistorySummary] = []
    @Published var selectedDetail: SessionHistoryDetail?
    @Published var actionMessage = ""
    @Published var architectErrorDetail: String?

    private let service: any SessionHistoryServing

    init(service: any SessionHistoryServing = PythonEngineBridgeService()) {
        self.service = service
    }

    func refresh() async {
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
        do {
            selectedDetail = try await service.getHistorySession(sessionID: session.sessionID)
            actionMessage = ""
        } catch {
            actionMessage = "Détail indisponible."
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
            }
        } catch {
            actionMessage = "Suppression locale impossible."
        }
    }

    func clearAll() async {
        do {
            let cleared = try await service.clearHistory()
            if cleared {
                sessions = []
                selectedDetail = nil
            }
        } catch {
            actionMessage = "Nettoyage impossible."
        }
    }

    func replayGeneration() async -> PlaylistGenerationResult? {
        guard let sessionID = selectedDetail?.summary.sessionID else { return nil }
        do {
            let result = try await service.replayGeneration(sessionID: sessionID)
            actionMessage = "Relance effectuée."
            return result
        } catch {
            actionMessage = "Relance impossible."
            return nil
        }
    }

    func exportSelection() async {
        guard let sessionID = selectedDetail?.summary.sessionID else { return }
        do {
            let export = try await service.exportHistorySession(sessionID: sessionID)
            if let export {
                actionMessage = "Export prêt: \(export.playlistName)"
            } else {
                actionMessage = "Export indisponible."
            }
        } catch {
            actionMessage = "Export impossible."
        }
    }

    private func message(for error: SessionHistoryServiceError) -> String {
        switch error {
        case .bridgeUnavailable:
            return """
            Moteur Python introuvable. Lance l'app depuis apps/resonance ou définis RESONANCE_REPO_ROOT.
            """
        case .timeout:
            return "Le moteur Python n'a pas répondu à temps."
        case .invalidResponse:
            return "Réponse bridge invalide pour l'historique."
        case .bridge(let payload):
            return payload.message
        }
    }
}
