import ResonanceCore
@testable import ResonanceMac
import XCTest

@MainActor
final class DiagnosticsViewModelTests: XCTestCase {
    func testRefreshLoadsDiagnosticsSnapshot() async {
        let service = StubDiagnosticsService()
        let viewModel = DiagnosticsViewModel(service: service)
        await viewModel.refresh()

        XCTAssertEqual(viewModel.screenState, .completed)
        XCTAssertEqual(viewModel.snapshot?.engineVersion, "1.2.3")
        XCTAssertEqual(viewModel.snapshot?.summary.bridgeStatus, "connected")
        XCTAssertEqual(viewModel.providers.count, 1)
    }

    func testArchitectModeShowsAllEvents() async {
        let service = StubDiagnosticsService()
        let viewModel = DiagnosticsViewModel(service: service)
        viewModel.displayMode = .architect
        await viewModel.refresh()

        XCTAssertEqual(viewModel.filteredEvents().count, 2)
    }

    func testSimpleModeHidesDebugEvents() async {
        let service = StubDiagnosticsService()
        let viewModel = DiagnosticsViewModel(service: service)
        viewModel.displayMode = .simple
        await viewModel.refresh()

        XCTAssertEqual(viewModel.filteredEvents().count, 1)
        XCTAssertEqual(viewModel.filteredEvents().first?.level, .info)
    }

    func testBridgeUnavailableShowsFailure() async {
        final class FailingDiagnosticsService: DiagnosticsServing {
            func fetchDiagnostics() async throws -> DiagnosticsSnapshot {
                throw DiagnosticsServiceError.bridgeUnavailable
            }

            func listProviders() async throws -> [ProviderOption] {
                []
            }
        }

        let viewModel = DiagnosticsViewModel(service: FailingDiagnosticsService())
        await viewModel.refresh()
        if case .failed(let message) = viewModel.screenState {
            XCTAssertTrue(message.contains("indisponible"))
        } else {
            XCTFail("Expected failed state")
        }
    }
}

private struct StubDiagnosticsService: DiagnosticsServing {
    func fetchDiagnostics() async throws -> DiagnosticsSnapshot {
        DiagnosticsSnapshot(
            engineVersion: "1.2.3",
            summary: DiagnosticsSummary(
                bridgeStatus: "connected",
                platform: "darwin",
                executionMS: 12,
                catalogCacheEntries: 4,
                identityCacheEntries: 2,
                catalogCacheEnabled: true,
                countryCode: "fr",
                activeProviders: [
                    ProviderOption(
                        providerID: .appleMusic,
                        displayName: "Apple Music",
                        isAvailable: true,
                        isConnected: true
                    ),
                ],
                recentReports: [],
                reportsDirectory: "reports"
            ),
            events: [
                DiagnosticEvent(phase: "bridge", message: "Connecté", level: .info),
                DiagnosticEvent(phase: "cache", message: "Debug", level: .debug),
            ]
        )
    }

    func listProviders() async throws -> [ProviderOption] {
        [
            ProviderOption(
                providerID: .appleMusic,
                displayName: "Apple Music",
                isAvailable: true,
                isConnected: true
            ),
        ]
    }
}
