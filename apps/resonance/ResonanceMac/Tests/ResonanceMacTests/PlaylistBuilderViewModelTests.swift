import ResonanceCore
import XCTest

@testable import ResonanceMac

@MainActor
final class PlaylistBuilderViewModelTests: XCTestCase {
    func testBuildRequestMapsFormFields() {
        let viewModel = PlaylistBuilderViewModel()
        viewModel.name = "Pool Party"
        viewModel.descriptionText = "Sunset vibes"
        viewModel.seedArtist = "Kygo"
        viewModel.seedTrack = "Firestone"
        viewModel.keywordsText = "tropical, deep house"
        viewModel.targetTrackCountText = "40"
        viewModel.energyProfile = .party

        let request = viewModel.buildRequest()
        XCTAssertEqual(request.name, "Pool Party")
        XCTAssertEqual(request.seeds.first?.artist, "Kygo")
        XCTAssertEqual(request.keywords, ["tropical", "deep house"])
        XCTAssertEqual(request.targetTrackCount, 40)
        XCTAssertEqual(request.energyCurve.profile, .party)
    }

    func testGenerateProducesPreview() async {
        let viewModel = PlaylistBuilderViewModel()
        viewModel.name = "Test Playlist"
        viewModel.seedArtist = "Artist"
        viewModel.seedTrack = "Track"
        viewModel.targetTrackCountText = "8"

        await viewModel.generate()

        XCTAssertEqual(viewModel.screenState, PlaylistBuilderViewModel.ScreenState.preview)
        XCTAssertNotNil(viewModel.previewResult)
        XCTAssertGreaterThan(viewModel.previewResult?.trackCount ?? 0, 0)
    }

    func testGenerateWithInvalidFormStaysEditing() async {
        let viewModel = PlaylistBuilderViewModel()
        viewModel.name = ""

        await viewModel.generate()

        XCTAssertEqual(viewModel.screenState, .editing)
        XCTAssertFalse(viewModel.validationErrors.isEmpty)
    }

    func testValidFormEnablesGenerate() {
        let viewModel = PlaylistBuilderViewModel()
        viewModel.name = "E2E Pool Party"
        viewModel.seedArtist = "Kygo"
        viewModel.seedTrack = "Firestone"
        viewModel.keywordsText = "summer, tropical, dance"
        viewModel.targetTrackCountText = "20"

        viewModel.validateForm()

        XCTAssertTrue(viewModel.isValid)
        XCTAssertTrue(viewModel.canGenerate)
    }
}
