import AppKit
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
    @Published var actionFeedback: String?

    private let service: any DiagnosticsServing

    init(service: any DiagnosticsServing = PythonEngineBridgeService()) {
        self.service = service
    }

    var modeIntroduction: String {
        switch displayMode {
        case .simple:
            return "Vue d'ensemble : état Apple Music, bridge et derniers problèmes détectés."
        case .architect:
            return "Vue technique : version moteur, chemins, providers, cache et événements bruts."
        }
    }

    var bridgeStatusLabel: String {
        guard let status = snapshot?.summary.bridgeStatus else { return "Inconnu" }
        switch status.lowercased() {
        case "connected": return "Connecté"
        case "disconnected": return "Déconnecté"
        default: return status
        }
    }

    var appleMusicStatusLabel: String {
        guard let provider = appleMusicProvider else { return "Indisponible" }
        if provider.isConnected { return "Connecté" }
        if provider.isAvailable { return "Disponible" }
        if provider.unavailableReason.isEmpty { return "Indisponible" }
        return provider.unavailableReason
    }

    var lastImportLabel: String {
        guard let report = snapshot?.summary.recentReports.first else {
            return "Aucun import récent enregistré."
        }
        return "«\(report.playlistName)» — +\(report.added) ajouté(s), \(report.notFound) introuvable(s), \(report.errors) erreur(s)"
    }

    var lastProblemLabel: String {
        let problems = filteredEvents().filter { $0.level == .warning || $0.level == .error }
        guard let latest = problems.last else { return "Aucun problème récent détecté." }
        return latest.message
    }

    var engineVersionLabel: String {
        snapshot?.engineVersion ?? "—"
    }

    var platformLabel: String {
        snapshot?.summary.platform ?? "—"
    }

    var pythonPathLabel: String {
        if let bridge = service as? PythonEngineBridgeService,
           let cwd = bridge.bridgeWorkingDirectory {
            return ResonancePaths.resolvePythonExecutable(repoRoot: URL(fileURLWithPath: cwd))
        }
        if let root = ResonancePaths.repoRoot() {
            return ResonancePaths.resolvePythonExecutable(repoRoot: root)
        }
        return "Non détecté"
    }

    var workingDirectoryLabel: String {
        if let bridge = service as? PythonEngineBridgeService {
            return bridge.bridgeWorkingDirectory ?? FileManager.default.currentDirectoryPath
        }
        return FileManager.default.currentDirectoryPath
    }

    var reportsDirectoryLabel: String {
        snapshot?.summary.reportsDirectory ?? "—"
    }

    private var appleMusicProvider: ProviderOption? {
        providers.first { $0.providerID == .appleMusic }
            ?? snapshot?.summary.activeProviders.first { $0.providerID == .appleMusic }
    }

    func refresh() async {
        screenState = .running
        architectErrorDetail = nil
        actionFeedback = nil
        do {
            async let diagnosticsTask = service.fetchDiagnostics()
            async let providersTask = service.listProviders()
            let diagnostics = try await diagnosticsTask
            let providerList = try await providersTask
            snapshot = diagnostics
            providers = providerList
            screenState = diagnostics.summary.bridgeStatus == "connected" ? .completed : .connected
            actionFeedback = "Diagnostics mis à jour."
        } catch let error as DiagnosticsServiceError {
            screenState = .failed(message(for: error))
            architectErrorDetail = architectDetail(for: error)
        } catch {
            screenState = .failed("Impossible de charger les diagnostics.")
            architectErrorDetail = String(describing: error)
        }
    }

    func testAppleMusic() async {
        actionFeedback = "Test Apple Music en cours…"
        await refresh()
        if case .failed(let message) = screenState {
            actionFeedback = message
            return
        }
        actionFeedback = "Apple Music : \(appleMusicStatusLabel) · Bridge : \(bridgeStatusLabel)"
    }

    func openReportsDirectory() {
        let path = reportsDirectoryLabel.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !path.isEmpty, path != "—" else {
            actionFeedback = "Dossier de rapports indisponible."
            return
        }
        let url: URL
        if path.hasPrefix("/") {
            url = URL(fileURLWithPath: path)
        } else if let repo = ResonancePaths.repoRoot() {
            url = repo.appendingPathComponent(path)
        } else {
            url = URL(fileURLWithPath: path)
        }
        NSWorkspace.shared.open(url)
        actionFeedback = "Dossier rapports ouvert."
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
            return ImportErrorHumanizer.humanizeBridgeMessage(payload.message)
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
