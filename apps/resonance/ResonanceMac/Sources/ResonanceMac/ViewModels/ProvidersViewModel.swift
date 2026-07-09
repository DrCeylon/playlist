import Foundation
import ResonanceCore

@MainActor
final class ProvidersViewModel: ObservableObject {
    @Published private(set) var providers: [ProviderOption] = []
    @Published private(set) var isBusy = false
    @Published var actionFeedback: String?

    private let service: any DiagnosticsServing

    init(service: any DiagnosticsServing = MockDiagnosticsService()) {
        self.service = service
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
            let snapshot = try await service.fetchDiagnostics()
            providers = snapshot.summary.activeProviders.isEmpty
                ? DefaultProviders.options
                : snapshot.summary.activeProviders
            actionFeedback = nil
        } catch {
            providers = DefaultProviders.options
            actionFeedback = "Providers chargés depuis la configuration locale."
        }
    }
}
