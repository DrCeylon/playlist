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

    func testLoadFromHistoryViaPendingEditRequest() {
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

        var selection: SidebarItem? = .history
        coordinator.requestEditFromHistory(
            request,
            selection: Binding(get: { selection }, set: { selection = $0 })
        )
        coordinator.applyPendingEditIfNeeded()

        XCTAssertEqual(coordinator.playlistBuilder.name, "Pending")
        XCTAssertEqual(selection, .newPlaylist)
        XCTAssertEqual(coordinator.activeRoute, .newPlaylist)
    }
}
