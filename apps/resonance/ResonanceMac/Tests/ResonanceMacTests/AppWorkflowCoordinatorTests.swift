import ResonanceCore
@testable import ResonanceMac
import XCTest

@MainActor
final class AppWorkflowCoordinatorTests: XCTestCase {
    func testCanStartProcessFalseWhileGenerating() async {
        let coordinator = AppWorkflowCoordinator(
            generationService: MockPlaylistGenerationService(),
            importService: MockPlaylistImportService()
        )
        coordinator.playlistBuilder.name = "Test"
        coordinator.playlistBuilder.seedArtist = ArtistRef(id: "a", displayName: "Artist")
        coordinator.playlistBuilder.screenState = .generating

        XCTAssertFalse(coordinator.canStartProcess())
    }

    func testCanStartProcessFalseWhileImporting() {
        let coordinator = AppWorkflowCoordinator(
            generationService: MockPlaylistGenerationService(),
            importService: MockPlaylistImportService()
        )
        coordinator.importWorkflow.screenState = .importing

        XCTAssertFalse(coordinator.canStartProcess())
    }

    func testRequestEditFromHistoryLoadsBuilderOnApply() {
        let coordinator = AppWorkflowCoordinator(
            generationService: MockPlaylistGenerationService(),
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
            generationService: MockPlaylistGenerationService(),
            importService: MockPlaylistImportService()
        )
        coordinator.importWorkflow.screenState = .importing

        XCTAssertEqual(coordinator.processBlockingLabel, "Processus en cours")
    }

    func testIsManagingSessionMatchesActiveImportPlaylist() {
        let coordinator = AppWorkflowCoordinator(
            generationService: MockPlaylistGenerationService(),
            importService: MockPlaylistImportService()
        )
        coordinator.importWorkflow.screenState = .importing
        coordinator.importWorkflow.progress.playlistName = "Live Session"

        let detail = SessionHistoryDetail(
            summary: SessionHistorySummary(
                sessionID: "s1",
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

        XCTAssertTrue(coordinator.isManagingSession(detail))
    }

    func testStartImportSetsActiveRouteToNewPlaylist() async {
        let coordinator = AppWorkflowCoordinator(
            generationService: MockPlaylistGenerationService(),
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
            generationService: MockPlaylistGenerationService(),
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
