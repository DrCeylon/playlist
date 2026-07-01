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

    private let service: any DiagnosticsServing

    init(service: any DiagnosticsServing = PythonEngineBridgeService()) {
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
        } catch {
            screenState = .failed("Impossible de charger les diagnostics.")
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
            return "Le moteur Python est indisponible. Vérifie l'installation du projet."
        case .timeout:
            return "Le moteur Python n'a pas répondu à temps."
        case .invalidResponse:
            return "Réponse bridge invalide."
        case .bridge(let payload):
            return payload.message
        }
    }
}
