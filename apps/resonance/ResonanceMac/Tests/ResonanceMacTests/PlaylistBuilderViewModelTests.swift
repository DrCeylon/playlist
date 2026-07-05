import ResonanceCore
import XCTest

@testable import ResonanceMac

@MainActor
final class PlaylistBuilderViewModelTests: XCTestCase {
    func testBuildRequestMapsFormFields() {
        let viewModel = PlaylistBuilderViewModel()
        viewModel.name = "Pool Party"
        viewModel.descriptionText = "Sunset vibes"
        viewModel.seedArtist = ArtistRef(id: "kygo", displayName: "Kygo")
        viewModel.seedTrack = TrackRef(id: "firestone", title: "Firestone", artistName: "Kygo")
        viewModel.keywords = [
            KeywordRef(id: "tropical", label: "tropical"),
            KeywordRef(id: "deep-house", label: "deep house"),
        ]
        viewModel.targetTrackCountText = "40"
        viewModel.energyProfile = .party

        let request = viewModel.buildRequest()
        XCTAssertEqual(request.name, "Pool Party")
        XCTAssertEqual(request.seeds.first?.artist, "Kygo")
        XCTAssertEqual(request.seeds.first?.title, "Firestone")
        XCTAssertEqual(request.keywords, ["tropical", "deep house"])
        XCTAssertEqual(request.targetTrackCount, 40)
        XCTAssertEqual(request.energyCurve.profile, .party)
    }

    func testGenerateProducesPreview() async {
        let viewModel = PlaylistBuilderViewModel()
        viewModel.name = "Test Playlist"
        viewModel.seedArtist = ArtistRef(id: "artist", displayName: "Artist")
        viewModel.seedTrack = TrackRef(id: "track", title: "Track", artistName: "Artist")
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
        viewModel.seedArtist = ArtistRef(id: "kygo", displayName: "Kygo")
        viewModel.seedTrack = TrackRef(id: "firestone", title: "Firestone", artistName: "Kygo")
        viewModel.keywords = [
            KeywordRef(id: "summer", label: "summer"),
            KeywordRef(id: "tropical", label: "tropical"),
            KeywordRef(id: "dance", label: "dance"),
        ]
        viewModel.targetTrackCountText = "20"

        viewModel.validateForm()

        XCTAssertTrue(viewModel.isValid)
        XCTAssertTrue(viewModel.canGenerate)
    }

    func testInspirationArtworkURLPrefersTrackArtwork() {
        let viewModel = PlaylistBuilderViewModel()
        let artistURL = URL(string: "https://example.com/artist.jpg")
        let trackURL = URL(string: "https://example.com/track.jpg")

        viewModel.seedArtist = ArtistRef(
            id: "kygo",
            displayName: "Kygo",
            artworkURL: artistURL
        )
        XCTAssertEqual(viewModel.inspirationArtworkURL, artistURL)

        viewModel.seedTrack = TrackRef(
            id: "firestone",
            title: "Firestone",
            artistName: "Kygo",
            artworkURL: trackURL
        )
        XCTAssertEqual(viewModel.inspirationArtworkURL, trackURL)
    }

    func testCanonicalRefsUpdatePublishedProperties() {
        let viewModel = PlaylistBuilderViewModel()
        let artist = ArtistRef(id: "kygo", displayName: "Kygo")
        let track = TrackRef(id: "firestone", title: "Firestone", artistName: "Kygo")
        let keywords = [
            KeywordRef(id: "summer", label: "summer"),
            KeywordRef(id: "tropical", label: "tropical"),
        ]

        viewModel.name = "E2E Pool Party"
        viewModel.seedArtist = artist
        viewModel.seedTrack = track
        viewModel.keywords = keywords
        viewModel.targetTrackCountText = "20"

        XCTAssertEqual(viewModel.seedArtist?.displayName, "Kygo")
        XCTAssertEqual(viewModel.seedTrack?.title, "Firestone")
        XCTAssertEqual(viewModel.keywords.map(\.label), ["summer", "tropical"])
        XCTAssertTrue(viewModel.hasSeedOrKeywords)

        viewModel.validateForm()
        XCTAssertTrue(viewModel.canGenerate)
    }

    func testLoadFromHistoryRestoresFormFields() {
        let viewModel = PlaylistBuilderViewModel()
        let request = PlaylistGenerationRequest(
            name: "Historique Demo",
            providerID: .appleMusic,
            seeds: [SeedReference(artist: "Daft Punk", title: "One More Time")],
            keywords: ["house", "disco"],
            description: "Soirée",
            targetTrackCount: 30,
            targetDurationMinutes: 90,
            energyCurve: EnergyCurveOption(profile: .party),
            exclusions: [ExclusionRule(kind: .artist, value: "Skrillex", reason: "Trop agressif")],
            playlistTheme: "house, disco"
        )

        viewModel.loadFromHistory(request)

        XCTAssertEqual(viewModel.name, "Historique Demo")
        XCTAssertEqual(viewModel.seedArtist?.displayName, "Daft Punk")
        XCTAssertEqual(viewModel.seedTrack?.title, "One More Time")
        XCTAssertEqual(viewModel.keywords.map(\.label), ["house", "disco"])
        XCTAssertEqual(viewModel.targetTrackCountText, "30")
        XCTAssertEqual(viewModel.targetDurationText, "90")
        XCTAssertEqual(viewModel.energyProfile, .party)
        XCTAssertEqual(viewModel.exclusions.count, 1)
        XCTAssertEqual(viewModel.screenState, .editing)
        XCTAssertNil(viewModel.previewResult)
    }
}
