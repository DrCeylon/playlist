import Foundation
import ResonanceCore

@MainActor
final class DiagnosticsViewModel: ObservableObject {
    enum ScreenState: Equatable {
        case disconnected
        case connected
        case running
        case completed
        case failed(String)
    }

    enum DisplayMode: String, CaseIterable, Identifiable {
        case simple
        case architect

        var id: String { rawValue }

        var title: String {
            switch self {
            case .simple: return "Simple"
            case .architect: return "Architecte"
            }
        }
    }

    @Published var screenState: ScreenState = .disconnected
    @Published var displayMode: DisplayMode = .simple
    @Published var snapshot: DiagnosticsSnapshot?
    @Published var providers: [ProviderOption] = []
    @Published var architectErrorDetail: String?

    private var service: any DiagnosticsServing

    init(service: any DiagnosticsServing = PythonEngineBridgeService()) {
        self.service = service
    }

    func replaceService(_ service: any DiagnosticsServing) {
        self.service = service
    }

    var bridgeStatusLabel: String {
        snapshot?.summary.bridgeStatus ?? "déconnecté"
    }

    var engineVersionLabel: String {
        snapshot?.engineVersion ?? "—"
    }

    func refresh() async {
        screenState = .running
        architectErrorDetail = nil
        do {
            async let diagnosticsTask = service.fetchDiagnostics()
            async let providersTask = service.listProviders()
            let diagnostics = try await diagnosticsTask
            let providerList = try await providersTask
            snapshot = diagnostics
            providers = providerList
            screenState = diagnostics.summary.bridgeStatus == "connected" ? .completed : .connected
        } catch let error as DiagnosticsServiceError {
            screenState = .failed(message(for: error))
            architectErrorDetail = architectDetail(for: error)
        } catch {
            screenState = .failed("Impossible de charger les diagnostics.")
            architectErrorDetail = String(describing: error)
        }
    }

    func filteredEvents() -> [DiagnosticEvent] {
        guard let events = snapshot?.events else { return [] }
        if displayMode == .simple {
            return events.filter { $0.level != .debug }
        }
        return events
    }

    private func message(for error: DiagnosticsServiceError) -> String {
        switch error {
        case .bridgeUnavailable:
            return """
            Moteur Python introuvable. Lance l'app depuis apps/resonance ou définis RESONANCE_REPO_ROOT.
            """
        case .timeout:
            return "Le moteur Python n'a pas répondu à temps."
        case .invalidResponse:
            return "Réponse bridge incomplète. Passe en mode Architecte pour les détails."
        case .bridge(let payload):
            return payload.message
        }
    }

    private func architectDetail(for error: DiagnosticsServiceError) -> String? {
        switch error {
        case .invalidResponse:
            return "Le payload diagnostics ne contient pas de section summary exploitable."
        case .bridge(let payload):
            return "\(payload.code.rawValue): \(payload.message)"
        case .bridgeUnavailable:
            if let bridge = service as? PythonEngineBridgeService {
                if bridge.isBridgeConfigured {
                    return "Bridge configuré (cwd: \(bridge.bridgeWorkingDirectory ?? "inconnu")) mais processus Python injoignable."
                }
                return "Aucune racine repo détectée (playlist_builder/). cwd=\(FileManager.default.currentDirectoryPath)"
            }
            return "Transport bridge non initialisé."
        case .timeout:
            return nil
        }
    }
}
