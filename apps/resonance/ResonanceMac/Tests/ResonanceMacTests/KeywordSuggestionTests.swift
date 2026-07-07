import XCTest
import ResonanceCore
@testable import ResonanceMac

final class KeywordSuggestionTests: XCTestCase {
    func testSuggestKeywordsFromArtistAndTrack() {
        let input = KeywordSuggestionInput(
            artistName: "Calvin Harris",
            trackTitle: "Summer",
            albumTitle: "Motion",
            releaseYear: 2014,
            primaryGenreName: "Dance"
        )

        let keywords = KeywordSuggestionEngine.suggestKeywords(from: input)

        XCTAssertTrue(keywords.contains("dance"))
        XCTAssertTrue(keywords.contains("summer"))
        XCTAssertTrue(keywords.contains("2010s"))
    }

    func testMergeAutomaticKeywordsPreservesManualAndAvoidsDuplicates() {
        let existing = [
            KeywordRef(id: "manual-summer", label: "summer", source: .manual),
            KeywordRef(id: "manual-chill", label: "chill", source: .manual),
        ]
        let suggested = [
            KeywordRef(id: "auto:dance", label: "dance", source: .autoGenre),
            KeywordRef(id: "auto:summer", label: "summer", source: .autoTrack),
        ]

        let merged = KeywordSuggestionEngine.mergeAutomaticKeywords(existing: existing, suggested: suggested)

        XCTAssertEqual(merged.filter { $0.label.lowercased() == "summer" }.count, 1)
        XCTAssertTrue(merged.contains(where: { $0.label == "dance" && $0.source == .autoGenre }))
        XCTAssertTrue(merged.contains(where: { $0.label == "chill" }))
    }

    func testSuggestKeywordRefsTagSourcesExplicitly() {
        let input = KeywordSuggestionInput(
            artistName: "Calvin Harris",
            trackTitle: "Summer",
            albumTitle: "Motion",
            releaseYear: 2014,
            primaryGenreName: "Dance"
        )

        let refs = KeywordSuggestionEngine.suggestKeywordRefs(from: input)

        XCTAssertTrue(refs.contains(where: { $0.label == "dance" && $0.source == .autoGenre }))
        XCTAssertTrue(refs.contains(where: { $0.label == "summer" && $0.source == .autoTrack }))
        XCTAssertTrue(refs.contains(where: { $0.label == "2010s" && $0.source == .autoYear }))
    }

    @MainActor
    func testPlaylistBuilderAddsAutomaticKeywordsAfterSelection() {
        let viewModel = PlaylistBuilderViewModel()
        viewModel.seedArtist = ArtistRef(id: "1", displayName: "Muse")
        viewModel.seedTrack = TrackRef(
            id: "2",
            title: "Butterflies & Hurricanes",
            artistName: "Muse",
            albumTitle: "Absolution",
            releaseYear: 2003,
            genreName: "Alternative Rock"
        )

        viewModel.mergeAutomaticKeywords()

        let keywords = viewModel.keywords
        XCTAssertFalse(keywords.isEmpty)
        XCTAssertTrue(keywords.contains(where: \.isAutomatic))
    }
}

@MainActor
final class ManualAcquisitionStatusTests: XCTestCase {
    func testConfirmManualAcquisitionRecordsClickTimestamp() async {
        final class ProbeService: PlaylistImportServing {
            func importPlaylist(
                _ result: PlaylistGenerationResult,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                ImportResultState(playlistName: result.playlistName, phase: .completed)
            }

            func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
                ImportResultState(playlistName: "Demo", phase: .completed)
            }

            func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
                ManualAcquisitionProbeResult(
                    found: false,
                    message: "Morceau pas encore détecté dans la bibliothèque. Vérifiez qu'il a bien été ajouté dans Music.app, puis réessayez.",
                    errorCode: "track_not_found"
                )
            }
        }

        let viewModel = ImportViewModel(service: ProbeService())
        viewModel.restoreManualAcquisition(
            from: ImportResultState(
                playlistName: "Demo",
                outcomes: [],
                phase: .waitingForManualAcquisition,
                importSessionID: "session-1",
                manualArtist: "Artist",
                manualTitle: "Title"
            ),
            generation: nil
        )

        await viewModel.confirmManualAcquisition()

        let status = viewModel.manualAcquisitionStatus
        XCTAssertNotNil(status.lastUserClickAt)
        let currentStep = status.currentStep
        XCTAssertTrue(
            currentStep.contains("non détecté") || currentStep.contains("Morceau")
        )
        XCTAssertFalse(status.lastVerificationResult.isEmpty)
    }
}
