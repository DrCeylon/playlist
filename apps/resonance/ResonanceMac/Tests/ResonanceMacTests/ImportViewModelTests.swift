import ResonanceCore
@testable import ResonanceMac
import XCTest

@MainActor
final class ImportViewModelTests: XCTestCase {
    func testImportSuccessShowsReport() async {
        let viewModel = ImportViewModel(service: MockPlaylistImportService())
        let generation = PlaylistGenerationResult(
            playlistName: "Demo",
            sections: [
                GeneratedSectionPreview(
                    name: "Main",
                    tracks: [GeneratedTrackPreview(artist: "Kygo", title: "Firestone", section: "Main", score: 0.9)]
                ),
            ],
            averageScore: 0.9
        )
        await viewModel.importPlaylist(generation)
        XCTAssertEqual(viewModel.screenState, .report)
        XCTAssertEqual(viewModel.report?.addedCount, 1)
    }

    func testManualAcquisitionPromptFromEvent() async {
        final class ManualImportService: PlaylistImportServing {
            func importPlaylist(
                _ result: PlaylistGenerationResult,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                onEvent(
                    BridgeEventMessage(
                        id: "import-1",
                        event: .manualAcquisitionRequired,
                        payload: [
                            "import_session_id": "session-1",
                            "token": "track-1",
                            "artist": "Kygo",
                            "title": "Firestone",
                            "instructions": "Ajoute le morceau dans Music.app",
                        ]
                    )
                )
                return ImportResultState(
                    playlistName: result.playlistName,
                    outcomes: [],
                    phase: .waitingForManualAcquisition
                )
            }

            func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
                ImportResultState(playlistName: "Demo", phase: .completed)
            }
        }

        let viewModel = ImportViewModel(service: ManualImportService())
        await viewModel.importPlaylist(
            PlaylistGenerationResult(playlistName: "Demo", sections: [], averageScore: 0)
        )
        XCTAssertEqual(viewModel.screenState, .waitingForManualAcquisition)
        XCTAssertEqual(viewModel.manualPrompt?.artist, "Kygo")
    }
}
