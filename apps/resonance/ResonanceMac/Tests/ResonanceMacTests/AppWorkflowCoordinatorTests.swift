import ResonanceCore
@testable import ResonanceMac
import XCTest

@MainActor
final class AppWorkflowCoordinatorTests: XCTestCase {
    func testCanStartProcessFalseWhileGenerating() async {
        let coordinator = AppWorkflowCoordinator(
            playlistGenerationService: MockPlaylistGenerationService(),
            importService: MockPlaylistImportService()
        )
        coordinator.playlistBuilder.name = "Test"
        coordinator.playlistBuilder.seedArtist = ArtistRef(id: "a", displayName: "Artist")
        coordinator.playlistBuilder.screenState = .generating

        XCTAssertFalse(coordinator.canStartProcess())
    }

    func testCanStartProcessFalseWhileImporting() {
        let coordinator = AppWorkflowCoordinator(
            playlistGenerationService: MockPlaylistGenerationService(),
            importService: MockPlaylistImportService()
        )
        coordinator.importWorkflow.screenState = .importing

        XCTAssertFalse(coordinator.canStartProcess())
    }

    func testRequestEditFromHistoryLoadsBuilderOnApply() {
        let coordinator = AppWorkflowCoordinator(
            playlistGenerationService: MockPlaylistGenerationService(),
            importService: MockPlaylistImportService()
        )
        let request = PlaylistGenerationRequest(
            name: "Pending",
            providerID: .appleMusic,
            seeds: [SeedReference(artist: "Artist", title: "")],
            keywords: ["chill"],
            description: "",
            targetTrackCount: 20,
            targetDurationMinutes: nil,
            energyCurve: EnergyCurveOption(profile: .rising),
            exclusions: [],
            playlistTheme: "chill"
        )

        coordinator.requestEditFromHistory(request)
        XCTAssertEqual(coordinator.activeRoute, .newPlaylist)
        coordinator.applyPendingEditIfNeeded()

        XCTAssertEqual(coordinator.playlistBuilder.name, "Pending")
        XCTAssertEqual(coordinator.activeRoute, .newPlaylist)
        XCTAssertNil(coordinator.pendingEditRequest)
    }

    func testProcessBlockingLabelWhileImporting() {
        let coordinator = AppWorkflowCoordinator(
            playlistGenerationService: MockPlaylistGenerationService(),
            importService: MockPlaylistImportService()
        )
        coordinator.importWorkflow.screenState = .importing

        XCTAssertEqual(coordinator.processBlockingLabel, "Processus en cours")
    }

    func testIsManagingSessionMatchesActiveImportPlaylist() async {
        let importService = ControllableImportService()
        let coordinator = AppWorkflowCoordinator(
            playlistGenerationService: MockPlaylistGenerationService(),
            importService: importService
        )
        let generation = PlaylistGenerationResult(
            playlistName: "Live Session",
            sections: [],
            averageScore: 0.8,
            providerID: .appleMusic,
            historySessionID: "hist-live"
        )

        let importTask = Task {
            await coordinator.startImport(from: generation)
        }
        await importService.waitUntilImportStarted()

        let detail = SessionHistoryDetail(
            summary: SessionHistorySummary(
                sessionID: "hist-live",
                startedAtISO: "2026-07-01",
                finishedAtISO: "2026-07-01",
                playlistName: "Live Session",
                providerID: .appleMusic,
                status: .generated,
                trackCount: 10,
                addedCount: 0,
                skippedCount: 0,
                notFoundCount: 0,
                errorCount: 0,
                durationMS: nil,
                textReportPath: "",
                jsonReportPath: ""
            )
        )

        XCTAssertEqual(coordinator.activeHistorySessionID, "hist-live")
        XCTAssertTrue(coordinator.isManagingSession(detail))
        XCTAssertTrue(coordinator.isProtectedHistorySession(detail.summary))

        importService.finish(with: ImportResultState(playlistName: "Live Session", outcomes: [], phase: .completed))
        _ = await importTask.result
    }

    func testActiveHistorySessionIDComesFromImportWorkflow() async {
        let importService = ControllableImportService()
        let coordinator = AppWorkflowCoordinator(
            playlistGenerationService: MockPlaylistGenerationService(),
            importService: importService
        )
        let generation = PlaylistGenerationResult(
            playlistName: "Import Demo",
            sections: [],
            averageScore: 0.8,
            providerID: .appleMusic,
            historySessionID: "hist-import"
        )

        let importTask = Task {
            await coordinator.startImport(from: generation)
        }
        await importService.waitUntilImportStarted()

        XCTAssertEqual(coordinator.activeHistorySessionID, "hist-import")
        XCTAssertEqual(coordinator.importWorkflow.activeHistorySessionID, "hist-import")

        importService.finish(with: ImportResultState(playlistName: "Import Demo", outcomes: [], phase: .completed))
        _ = await importTask.result
    }

    func testStartImportSetsActiveRouteToNewPlaylist() async {
        let coordinator = AppWorkflowCoordinator(
            playlistGenerationService: MockPlaylistGenerationService(),
            importService: MockPlaylistImportService()
        )
        let generation = PlaylistGenerationResult(
            playlistName: "Import Demo",
            sections: [],
            averageScore: 0.8,
            providerID: .appleMusic
        )

        await coordinator.startImport(from: generation)

        XCTAssertEqual(coordinator.activeRoute, .newPlaylist)
        XCTAssertEqual(coordinator.importWorkflow.screenState, .report)
    }

    func testBannerPresentationIncludesSubstepsFromImportDiagnostics() {
        let coordinator = AppWorkflowCoordinator(
            playlistGenerationService: MockPlaylistGenerationService(),
            importService: MockPlaylistImportService()
        )
        coordinator.importWorkflow.screenState = .importing
        coordinator.importWorkflow.progress = ImportProgressSnapshot(
            playlistName: "Diagnostics Demo",
            diagnostics: ["Étape bridge", "Résolution 1/3"]
        )

        XCTAssertEqual(coordinator.banner?.substeps.count, 2)
        XCTAssertEqual(coordinator.banner?.playlistName, "Diagnostics Demo")
    }
}

@MainActor
private final class ControllableImportService: PlaylistImportServing, @unchecked Sendable {
    private var resumeImport: ((Result<ImportResultState, Error>) -> Void)?
    private var importHasStarted = false
    private var startedWaiters: [CheckedContinuation<Void, Never>] = []

    func waitUntilImportStarted() async {
        if importHasStarted { return }
        await withCheckedContinuation { continuation in
            if importHasStarted {
                continuation.resume()
            } else {
                startedWaiters.append(continuation)
            }
        }
    }

    private func signalImportStarted() {
        importHasStarted = true
        for waiter in startedWaiters {
            waiter.resume()
        }
        startedWaiters.removeAll()
    }

    func importPlaylist(
        _ result: PlaylistGenerationResult,
        onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
    ) async throws -> ImportResultState {
        onEvent(
            BridgeEventMessage(
                id: "controllable-import",
                event: .progress,
                payload: [
                    "phase": .string(ImportPhase.resolving.rawValue),
                    "total_tracks": .number(Double(result.trackCount)),
                    "processed_tracks": .number(0),
                ]
            )
        )
        signalImportStarted()

        return try await withCheckedThrowingContinuation { continuation in
            resumeImport = { continuation.resume(with: $0) }
        }
    }

    func finish(with result: ImportResultState) {
        resumeImport?(.success(result))
        resumeImport = nil
    }

    func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
        _ = importSessionID
        throw PlaylistImportError.bridgeUnavailable
    }

    func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
        _ = importSessionID
        return ManualAcquisitionProbeResult(found: false)
    }
}
