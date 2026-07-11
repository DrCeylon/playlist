import Foundation
import ResonanceCore

@MainActor
final class ProvidersViewModel: ObservableObject {
    @Published private(set) var providers: [ProviderOption] = []
    @Published private(set) var isBusy = false
    @Published var actionFeedback: String?

    private let diagnosticsService: any DiagnosticsServing
    private let platformService: any ProviderPlatformServing

    init(
        diagnosticsService: any DiagnosticsServing,
        platformService: any ProviderPlatformServing
    ) {
        self.diagnosticsService = diagnosticsService
        self.platformService = platformService
    }

    var primaryProviders: [ProviderOption] {
        providers.filter { !$0.isExperimental }
    }

    var experimentalProviders: [ProviderOption] {
        providers.filter(\.isExperimental)
    }

    func refresh() async {
        isBusy = true
        defer { isBusy = false }
        do {
            let snapshot = try await diagnosticsService.fetchDiagnostics()
            providers = snapshot.summary.activeProviders.isEmpty
                ? DefaultProviders.options
                : snapshot.summary.activeProviders
            actionFeedback = nil
        } catch {
            providers = DefaultProviders.options
            actionFeedback = "Services chargés depuis la configuration locale."
        }
    }

    func connect(providerID: ProviderID) async {
        isBusy = true
        defer { isBusy = false }
        do {
            _ = try await platformService.providerConnect(providerID: providerID, params: [:])
            actionFeedback = "Connexion demandée — suivez les instructions si nécessaire."
            await refresh()
        } catch {
            actionFeedback = "Connexion impossible pour le moment."
        }
    }

    func disconnect(providerID: ProviderID) async {
        isBusy = true
        defer { isBusy = false }
        do {
            _ = try await platformService.providerDisconnect(providerID: providerID)
            actionFeedback = "Service déconnecté."
            await refresh()
        } catch {
            actionFeedback = "Déconnexion impossible."
        }
    }

    func supportsAuthentication(_ provider: ProviderOption) -> Bool {
        provider.capabilities.contains(.authentication)
    }
}
