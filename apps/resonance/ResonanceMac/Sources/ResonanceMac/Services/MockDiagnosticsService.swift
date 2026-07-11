import Foundation
import ResonanceCore

public struct MockDiagnosticsService: DiagnosticsServing {
    public init() {}

    public func fetchDiagnostics() async throws -> DiagnosticsSnapshot {
        DiagnosticsSnapshot(
            engineVersion: "mock",
            summary: DiagnosticsSummary(
                bridgeStatus: "mock",
                platform: "mock",
                executionMS: 1,
                catalogCacheEntries: 0,
                identityCacheEntries: 0,
                catalogCacheEnabled: true,
                countryCode: "fr",
                activeProviders: DefaultProviders.options,
                recentReports: [],
                reportsDirectory: "reports"
            ),
            events: [
                DiagnosticEvent(
                    phase: "bridge",
                    message: "Diagnostics mock",
                    level: .info
                ),
            ]
        )
    }

    public func listProviders() async throws -> [ProviderOption] {
        DefaultProviders.options
    }
}

extension MockDiagnosticsService: ProviderPlatformServing {
    public func providerConnect(providerID: ProviderID, params: [String: String]) async throws -> RemoteProviderAccount? { nil }

    public func providerDisconnect(providerID: ProviderID) async throws -> RemoteProviderAccount? { nil }
}
