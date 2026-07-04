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
}
