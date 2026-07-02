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
                            "import_session_id": .string("session-1"),
                            "token": .string("track-1"),
                            "artist": .string("Kygo"),
                            "title": .string("Firestone"),
                            "instructions": .string("Ajoute le morceau dans Music.app"),
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

    func testImportFailedShowsHumanReadableMessage() async {
        final class FailingImportService: PlaylistImportServing {
            func importPlaylist(
                _ result: PlaylistGenerationResult,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                throw NSError(
                    domain: NSCocoaErrorDomain,
                    code: 3840,
                    userInfo: [NSLocalizedDescriptionKey: "The data couldn't be read because it isn't in the correct format."]
                )
            }

            func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
                throw PlaylistImportError.invalidResponse
            }
        }

        let viewModel = ImportViewModel(service: FailingImportService())
        await viewModel.importPlaylist(
            PlaylistGenerationResult(playlistName: "Demo", sections: [], averageScore: 0)
        )
        if case .failed(let message) = viewModel.screenState {
            XCTAssertFalse(message.contains("couldn't be read"))
            XCTAssertTrue(message.contains("Réponse bridge invalide"))
        } else {
            XCTFail("Expected failed import state")
        }
        XCTAssertNotNil(viewModel.architectErrorDetail)
    }

    func testDiagnosticsRingBufferLimitsGrowth() async {
        final class ChattyImportService: PlaylistImportServing {
            func importPlaylist(
                _ result: PlaylistGenerationResult,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                for index in 0..<20 {
                    await MainActor.run {
                        onEvent(
                            BridgeEventMessage(
                                id: "diag-\(index)",
                                event: .diagnostic,
                                payload: [
                                    "message": .string("Music.app étape \(index)"),
                                ]
                            )
                        )
                    }
                }
                return ImportResultState(playlistName: result.playlistName, phase: .completed)
            }

            func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
                ImportResultState(playlistName: "Demo", phase: .completed)
            }
        }

        let viewModel = ImportViewModel(service: ChattyImportService())
        await viewModel.importPlaylist(
            PlaylistGenerationResult(playlistName: "Demo", sections: [], averageScore: 0)
        )
        XCTAssertLessThanOrEqual(
            viewModel.progress.diagnostics.count,
            ImportProgressSnapshot.maxVisibleDiagnostics
        )
    }

    func testImportPartialSuccessDecodableFromBridgePayload() throws {
        let payload: BridgeJSONObject = [
            "import": .object([
                "playlist_name": .string("Demo"),
                "phase": .string("partial_success"),
                "outcomes": .array([
                    .object([
                        "artist": .string("A"),
                        "title": .string("B"),
                        "section": .string("Main"),
                        "status": .string("added"),
                        "message": .string(""),
                    ]),
                    .object([
                        "artist": .string("C"),
                        "title": .string("D"),
                        "section": .string("Main"),
                        "status": .string("not_found"),
                        "message": .string("Introuvable dans Apple Music"),
                    ]),
                ]),
            ]),
        ]
        let result = try BridgePayloadBuilder.importResult(from: payload)
        XCTAssertEqual(result.phase, .partialSuccess)
        XCTAssertEqual(result.addedCount, 1)
        XCTAssertEqual(result.notFoundCount, 1)
    }
}
