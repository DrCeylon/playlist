import ResonanceCore
@testable import ResonanceMac
import XCTest

@MainActor
final class HistoryViewModelTests: XCTestCase {
    func testRefreshSuccessLoadsSessions() async {
        let service = StubHistoryService()
        let viewModel = HistoryViewModel(service: service)
        await viewModel.refresh()
        XCTAssertEqual(viewModel.screenState, .ready)
        XCTAssertEqual(viewModel.sessions.count, 1)
    }

    func testRefreshErrorShowsFailure() async {
        let viewModel = HistoryViewModel(service: FailingHistoryService())
        await viewModel.refresh()
        if case .failed = viewModel.screenState {
            XCTAssertTrue(true)
        } else {
            XCTFail("Expected failure state")
        }
    }

    func testRefreshEmptyHistoryShowsReadyState() async {
        let viewModel = HistoryViewModel(service: EmptyHistoryService())
        await viewModel.refresh()
        XCTAssertEqual(viewModel.screenState, .ready)
        XCTAssertTrue(viewModel.sessions.isEmpty)
    }

    func testBridgeUnavailableShowsUsefulMessage() async {
        let viewModel = HistoryViewModel(service: UnavailableHistoryService())
        await viewModel.refresh()
        if case .failed(let message) = viewModel.screenState {
            XCTAssertTrue(message.contains("Moteur Python introuvable"))
        } else {
            XCTFail("Expected bridge unavailable failure")
        }
    }

    func testSessionDetailMappingAndRetryAction() async {
        let service = StubHistoryService()
        let viewModel = HistoryViewModel(service: service)
        await viewModel.refresh()
        guard let session = viewModel.sessions.first else {
            XCTFail("Expected one session")
            return
        }
        await viewModel.select(session: session)
        XCTAssertEqual(viewModel.selectedDetail?.summary.sessionID, session.sessionID)
        await viewModel.retryGeneration()
        if case .success(let message) = viewModel.actionFeedback {
            XCTAssertTrue(message.contains("régénérée"))
        } else {
            XCTFail("Expected retry success feedback")
        }
    }

    func testRetryWithoutRequestShowsClearFailure() async {
        let service = StubHistoryService(generationRequest: [:])
        let viewModel = HistoryViewModel(service: service)
        await viewModel.refresh()
        await viewModel.select(session: viewModel.sessions.first!)
        await viewModel.retryGeneration()
        if case .failure(let message) = viewModel.actionFeedback {
            XCTAssertTrue(message.contains("Paramètres"))
        } else {
            XCTFail("Expected retry failure feedback")
        }
    }

    func testImportWithoutPreviewShowsClearFailure() async {
        let service = StubHistoryService(generationResult: [:])
        let viewModel = HistoryViewModel(service: service, importService: StubImportService())
        await viewModel.refresh()
        await viewModel.select(session: viewModel.sessions.first!)
        await viewModel.importSelected()
        if case .failure(let message) = viewModel.actionFeedback {
            XCTAssertTrue(message.contains("Preview indisponible") || message.contains("insuffisantes"))
        } else {
            XCTFail("Expected import failure feedback")
        }
    }

    func testPreparePlaylistPreviewLoadsGenerationResult() async {
        let service = StubHistoryService()
        let viewModel = HistoryViewModel(service: service)
        await viewModel.refresh()
        await viewModel.select(session: viewModel.sessions.first!)
        viewModel.preparePlaylistPreview()
        XCTAssertEqual(viewModel.playlistPreview?.playlistName, "Demo")
    }

    func testEditRequestMapsStoredPayload() async {
        let service = StubHistoryService()
        let viewModel = HistoryViewModel(service: service)
        await viewModel.refresh()
        await viewModel.select(session: viewModel.sessions.first!)
        let request = viewModel.editRequestForSelectedSession()
        XCTAssertEqual(request?.name, "Demo")
        XCTAssertEqual(request?.seeds.first?.artist, "Kygo")
        XCTAssertEqual(request?.keywords, ["pool"])
    }

    func testStatusLabelsAreFrench() {
        XCTAssertEqual(SessionHistoryDisplay.statusLabel(for: .generated), "Générée")
        XCTAssertEqual(SessionHistoryDisplay.statusLabel(for: .waitingForManualAcquisition), "Action manuelle requise")
    }

    func testExportShowsSuccessFeedback() async {
        let service = StubHistoryService()
        let viewModel = HistoryViewModel(service: service)
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

private struct StubHistoryService: SessionHistoryServing {
    var generationRequest: BridgeJSONObject = [
        "name": .string("Demo"),
        "provider_id": .string("apple_music"),
        "seeds": .array([
            .object(["artist": .string("Kygo"), "title": .string("Firestone"), "weight": .number(1)]),
        ]),
        "keywords": .array([.string("pool")]),
        "target_track_count": .number(50),
    ]
    var generationResult: BridgeJSONObject = [
        "playlist_name": .string("Demo"),
        "sections": .array([]),
        "average_score": .number(0.8),
        "provider_id": .string("apple_music"),
    ]

    func listHistory() async throws -> [SessionHistorySummary] {
        [
            SessionHistorySummary(
                sessionID: "hist-1",
                startedAtISO: "2026-07-02T08:00:00",
                finishedAtISO: "2026-07-02T08:01:00",
                playlistName: "Demo",
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
            generationRequest: generationRequest,
            generationResult: generationResult
        )
    }

    func deleteHistorySession(sessionID: String) async throws -> Bool { true }
    func clearHistory() async throws -> Bool { true }

    func replayGeneration(sessionID: String) async throws -> PlaylistGenerationResult {
        PlaylistGenerationResult(playlistName: "Replay Demo", sections: [], averageScore: 0.7, providerID: .appleMusic)
    }

    func exportHistorySession(sessionID: String) async throws -> SessionHistoryExport? {
        SessionHistoryExport(
            sessionID: sessionID,
            playlistName: "Demo",
            providerID: .appleMusic,
            status: .generated,
            textReportPath: "",
            jsonReportPath: ""
        )
    }
}

private struct StubImportService: PlaylistImportServing {
    func importPlaylist(
        _ result: PlaylistGenerationResult,
        onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
    ) async throws -> ImportResultState {
        ImportResultState(playlistName: result.playlistName, phase: .completed)
    }

    func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
        throw PlaylistImportError.bridgeUnavailable
    }
}

private struct FailingHistoryService: SessionHistoryServing {
    func listHistory() async throws -> [SessionHistorySummary] { throw NSError(domain: "test", code: 1) }
    func getHistorySession(sessionID: String) async throws -> SessionHistoryDetail? { nil }
    func deleteHistorySession(sessionID: String) async throws -> Bool { false }
    func clearHistory() async throws -> Bool { false }
    func replayGeneration(sessionID: String) async throws -> PlaylistGenerationResult { throw NSError(domain: "test", code: 2) }
    func exportHistorySession(sessionID: String) async throws -> SessionHistoryExport? { nil }
}

private struct EmptyHistoryService: SessionHistoryServing {
    func listHistory() async throws -> [SessionHistorySummary] { [] }
    func getHistorySession(sessionID: String) async throws -> SessionHistoryDetail? { nil }
    func deleteHistorySession(sessionID: String) async throws -> Bool { false }
    func clearHistory() async throws -> Bool { false }
    func replayGeneration(sessionID: String) async throws -> PlaylistGenerationResult { throw NSError(domain: "test", code: 2) }
    func exportHistorySession(sessionID: String) async throws -> SessionHistoryExport? { nil }
}

private struct UnavailableHistoryService: SessionHistoryServing {
    func listHistory() async throws -> [SessionHistorySummary] {
        throw SessionHistoryServiceError.bridgeUnavailable
    }
    func getHistorySession(sessionID: String) async throws -> SessionHistoryDetail? { nil }
    func deleteHistorySession(sessionID: String) async throws -> Bool { false }
    func clearHistory() async throws -> Bool { false }
    func replayGeneration(sessionID: String) async throws -> PlaylistGenerationResult { throw SessionHistoryServiceError.bridgeUnavailable }
    func exportHistorySession(sessionID: String) async throws -> SessionHistoryExport? { nil }
}
