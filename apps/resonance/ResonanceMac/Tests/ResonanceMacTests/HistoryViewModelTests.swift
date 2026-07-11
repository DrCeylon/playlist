import ResonanceCore
@testable import ResonanceMac
import XCTest

@MainActor
final class HistoryViewModelTests: XCTestCase {
    func testRefreshSuccessLoadsSessions() async {
        let service = StubHistoryService()
        let viewModel = HistoryViewModel(service: service, importService: MockPlaylistImportService())
        await viewModel.refresh()
        XCTAssertEqual(viewModel.screenState, .ready)
        XCTAssertEqual(viewModel.sessions.count, 1)
    }

    func testRefreshErrorShowsFailure() async {
        let viewModel = HistoryViewModel(service: FailingHistoryService(), importService: MockPlaylistImportService())
        await viewModel.refresh()
        if case .failed = viewModel.screenState {
            XCTAssertTrue(true)
        } else {
            XCTFail("Expected failure state")
        }
    }

    func testRefreshEmptyHistoryShowsReadyState() async {
        let viewModel = HistoryViewModel(service: EmptyHistoryService(), importService: MockPlaylistImportService())
        await viewModel.refresh()
        XCTAssertEqual(viewModel.screenState, .ready)
        XCTAssertTrue(viewModel.sessions.isEmpty)
    }

    func testBridgeUnavailableShowsUsefulMessage() async {
        let viewModel = HistoryViewModel(service: UnavailableHistoryService(), importService: MockPlaylistImportService())
        await viewModel.refresh()
        if case .failed(let message) = viewModel.screenState {
            XCTAssertTrue(message.contains("Moteur Python introuvable"))
        } else {
            XCTFail("Expected bridge unavailable failure")
        }
    }

    func testResumeContentShowsPreviewForGeneratedSession() async {
        let service = StubHistoryService()
        let viewModel = HistoryViewModel(service: service, importService: MockPlaylistImportService())
        await viewModel.refresh()
        await viewModel.select(session: viewModel.sessions.first!)
        if case .preview(let result) = viewModel.resumeContent {
            XCTAssertEqual(result.playlistName, "Demo")
        } else {
            XCTFail("Expected preview resume content")
        }
    }

    func testResumeContentShowsImportReportForImportedSession() async {
        let service = StubHistoryService(
            status: .imported,
            importResult: StubHistoryService.sampleImportResult
        )
        let viewModel = HistoryViewModel(service: service, importService: MockPlaylistImportService())
        await viewModel.refresh()
        await viewModel.select(session: viewModel.sessions.first!)
        if case .importReport(let report) = viewModel.resumeContent {
            XCTAssertEqual(report.playlistName, "Demo")
            XCTAssertEqual(report.addedCount, 3)
        } else {
            XCTFail("Expected import report resume content")
        }
    }

    func testResumeContentUnavailableWithoutPreview() async {
        let service = StubHistoryService(generationResult: [:])
        let viewModel = HistoryViewModel(service: service, importService: MockPlaylistImportService())
        await viewModel.refresh()
        await viewModel.select(session: viewModel.sessions.first!)
        if case .unavailable(let hasRequest, let playlistName) = viewModel.resumeContent {
            XCTAssertTrue(hasRequest)
            XCTAssertEqual(playlistName, "Demo")
        } else {
            XCTFail("Expected unavailable resume content")
        }
    }

    func testEditRequestForSelectedSession() async {
        let service = StubHistoryService()
        let viewModel = HistoryViewModel(service: service, importService: MockPlaylistImportService())
        await viewModel.refresh()
        await viewModel.select(session: viewModel.sessions.first!)
        XCTAssertEqual(viewModel.editRequestForSelectedSession()?.name, "Demo")
    }

    func testClearAllPreservesActiveSession() async {
        let service = MultiSessionHistoryService()
        let viewModel = HistoryViewModel(service: service, importService: MockPlaylistImportService())
        await viewModel.refresh()
        XCTAssertEqual(viewModel.sessions.count, 2)

        await viewModel.clearAll(preservingSessionID: "hist-active")

        XCTAssertEqual(viewModel.sessions.count, 1)
        XCTAssertEqual(viewModel.sessions.first?.sessionID, "hist-active")
        if case .success(let message) = viewModel.actionFeedback {
            XCTAssertTrue(message.contains("conservée"))
        } else {
            XCTFail("Expected partial clear success feedback")
        }
    }

    func testDeleteProtectedSessionShowsFailure() async {
        let service = MultiSessionHistoryService()
        let viewModel = HistoryViewModel(service: service, importService: MockPlaylistImportService())
        await viewModel.refresh()
        let active = viewModel.sessions.first { $0.sessionID == "hist-active" }!

        await viewModel.delete(session: active, isProtected: { $0.sessionID == "hist-active" })

        if case .failure(let message) = viewModel.actionFeedback {
            XCTAssertTrue(message.contains("processus actif"))
        } else {
            XCTFail("Expected protected delete failure")
        }
        XCTAssertEqual(viewModel.sessions.count, 2)
    }

    func testExportShowsSuccessFeedback() async {
        let service = StubHistoryService()
        let viewModel = HistoryViewModel(service: service, importService: MockPlaylistImportService())
        await viewModel.refresh()
        await viewModel.select(session: viewModel.sessions.first!)
        await viewModel.exportSelection()
        if case .success = viewModel.actionFeedback {
            XCTAssertTrue(true)
        } else if case .failure = viewModel.actionFeedback {
            XCTFail("Export should succeed for stub session")
        } else {
            XCTFail("Expected export feedback")
        }
    }
}

private struct MultiSessionHistoryService: SessionHistoryServing {
    func listHistory() async throws -> [SessionHistorySummary] {
        [
            SessionHistorySummary(
                sessionID: "hist-active",
                startedAtISO: "2026-07-02T08:00:00",
                finishedAtISO: "2026-07-02T08:01:00",
                playlistName: "Active Import",
                providerID: .appleMusic,
                status: .generated,
                trackCount: 5,
                addedCount: 0,
                skippedCount: 0,
                notFoundCount: 0,
                errorCount: 0,
                durationMS: 1000,
                textReportPath: "",
                jsonReportPath: ""
            ),
            SessionHistorySummary(
                sessionID: "hist-old",
                startedAtISO: "2026-07-01T08:00:00",
                finishedAtISO: "2026-07-01T08:01:00",
                playlistName: "Old Session",
                providerID: .appleMusic,
                status: .imported,
                trackCount: 3,
                addedCount: 3,
                skippedCount: 0,
                notFoundCount: 0,
                errorCount: 0,
                durationMS: 900,
                textReportPath: "",
                jsonReportPath: ""
            ),
        ]
    }

    func getHistorySession(sessionID: String) async throws -> SessionHistoryDetail? { nil }
    func deleteHistorySession(sessionID: String) async throws -> Bool { true }
    func clearHistory() async throws -> Bool { true }
    func exportHistorySession(sessionID: String) async throws -> SessionHistoryExport? { nil }
}

private struct StubHistoryService: SessionHistoryServing {
    static let sampleImportResult: BridgeJSONObject = [
        "playlist_name": .string("Demo"),
        "phase": .string("completed"),
        "outcomes": .array([
            .object([
                "artist": .string("Artist A"),
                "title": .string("Track 1"),
                "status": .string("added"),
            ]),
            .object([
                "artist": .string("Artist B"),
                "title": .string("Track 2"),
                "status": .string("added"),
            ]),
            .object([
                "artist": .string("Artist C"),
                "title": .string("Track 3"),
                "status": .string("added"),
            ]),
            .object([
                "artist": .string("Artist D"),
                "title": .string("Track 4"),
                "status": .string("not_found"),
            ]),
        ]),
    ]

    var generationRequest: BridgeJSONObject = ["name": .string("Demo")]
    var generationResult: BridgeJSONObject = [
        "playlist_name": .string("Demo"),
        "sections": .array([]),
        "average_score": .number(0.8),
        "provider_id": .string("apple_music"),
    ]
    var importResult: BridgeJSONObject = [:]
    var status: SessionHistoryStatus = .generated

    init(
        generationRequest: BridgeJSONObject = ["name": .string("Demo")],
        generationResult: BridgeJSONObject = [
            "playlist_name": .string("Demo"),
            "sections": .array([]),
            "average_score": .number(0.8),
            "provider_id": .string("apple_music"),
        ],
        status: SessionHistoryStatus = .generated,
        importResult: BridgeJSONObject = [:]
    ) {
        self.generationRequest = generationRequest
        self.generationResult = generationResult
        self.status = status
        self.importResult = importResult
    }

    func listHistory() async throws -> [SessionHistorySummary] {
        [
            SessionHistorySummary(
                sessionID: "hist-1",
                startedAtISO: "2026-07-02T08:00:00",
                finishedAtISO: "2026-07-02T08:01:00",
                playlistName: "Demo",
                providerID: .appleMusic,
                status: status,
                trackCount: 5,
                addedCount: 0,
                skippedCount: 0,
                notFoundCount: 0,
                errorCount: 0,
                durationMS: 1000,
                textReportPath: "",
                jsonReportPath: ""
            ),
        ]
    }

    func getHistorySession(sessionID: String) async throws -> SessionHistoryDetail? {
        SessionHistoryDetail(
            summary: SessionHistorySummary(
                sessionID: sessionID,
                startedAtISO: "2026-07-02T08:00:00",
                finishedAtISO: "2026-07-02T08:01:00",
                playlistName: "Demo",
                providerID: .appleMusic,
                status: status,
                trackCount: 5,
                addedCount: status == .imported ? 3 : 0,
                skippedCount: 0,
                notFoundCount: status == .imported ? 1 : 0,
                errorCount: 0,
                durationMS: 1000,
                textReportPath: "",
                jsonReportPath: ""
            ),
            generationRequest: generationRequest,
            generationResult: generationResult,
            importResult: importResult
        )
    }

    func deleteHistorySession(sessionID: String) async throws -> Bool { true }
    func clearHistory() async throws -> Bool { true }

    func exportHistorySession(sessionID: String) async throws -> SessionHistoryExport? {
        SessionHistoryExport(
            sessionID: sessionID,
            playlistName: "Demo",
            providerID: .appleMusic,
            status: status,
            textReportPath: "",
            jsonReportPath: ""
        )
    }
}

private struct FailingHistoryService: SessionHistoryServing {
    func listHistory() async throws -> [SessionHistorySummary] { throw NSError(domain: "test", code: 1) }
    func getHistorySession(sessionID: String) async throws -> SessionHistoryDetail? { nil }
    func deleteHistorySession(sessionID: String) async throws -> Bool { false }
    func clearHistory() async throws -> Bool { false }
    func exportHistorySession(sessionID: String) async throws -> SessionHistoryExport? { nil }
}

private struct EmptyHistoryService: SessionHistoryServing {
    func listHistory() async throws -> [SessionHistorySummary] { [] }
    func getHistorySession(sessionID: String) async throws -> SessionHistoryDetail? { nil }
    func deleteHistorySession(sessionID: String) async throws -> Bool { false }
    func clearHistory() async throws -> Bool { false }
    func exportHistorySession(sessionID: String) async throws -> SessionHistoryExport? { nil }
}

private struct UnavailableHistoryService: SessionHistoryServing {
    func listHistory() async throws -> [SessionHistorySummary] {
        throw SessionHistoryServiceError.bridgeUnavailable
    }
    func getHistorySession(sessionID: String) async throws -> SessionHistoryDetail? { nil }
    func deleteHistorySession(sessionID: String) async throws -> Bool { false }
    func clearHistory() async throws -> Bool { false }
    func exportHistorySession(sessionID: String) async throws -> SessionHistoryExport? { nil }
}
