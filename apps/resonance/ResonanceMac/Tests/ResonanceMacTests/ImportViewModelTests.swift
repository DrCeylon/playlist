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

            func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
                ManualAcquisitionProbeResult(found: false)
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

            func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
                ManualAcquisitionProbeResult(found: false)
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

    func testTrackProgressUpdatesActivities() async {
        final class TrackProgressImportService: PlaylistImportServing {
            func importPlaylist(
                _ result: PlaylistGenerationResult,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                onEvent(
                    BridgeEventMessage(
                        id: "import-1",
                        event: .trackProgress,
                        payload: [
                            "track_key": .string("0:kygo:firestone"),
                            "track_index": .number(0),
                            "artist": .string("Kygo"),
                            "title": .string("Firestone"),
                            "step": .string("searching"),
                            "status": .string("pending"),
                            "message": .string("Recherche…"),
                            "is_current": .bool(true),
                        ]
                    )
                )
                return ImportResultState(playlistName: result.playlistName, phase: .completed)
            }

            func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
                ImportResultState(playlistName: "Demo", phase: .completed)
            }

            func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
                ManualAcquisitionProbeResult(found: false)
            }
        }

        let viewModel = ImportViewModel(service: TrackProgressImportService())
        await viewModel.importPlaylist(
            PlaylistGenerationResult(playlistName: "Demo", sections: [], averageScore: 0)
        )
        XCTAssertEqual(viewModel.screenState, .report)
        XCTAssertEqual(viewModel.progress.activities.count, 1)
        XCTAssertEqual(viewModel.progress.activities[0].title, "Firestone")
        XCTAssertEqual(
            viewModel.progress.currentStep,
            "Playlist créée — 0 morceau(x) ajouté(s)",
            "After import completes, progress should show the final summary step, not the last per-track message."
        )
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

            func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
                ManualAcquisitionProbeResult(found: false)
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

    func testRestoreManualAcquisitionFromHistoryReport() {
        let viewModel = ImportViewModel()
        let report = ImportResultState(
            playlistName: "Test au lit",
            outcomes: [
                ImportTrackOutcome(
                    artist: "Artist",
                    title: "Title",
                    section: "Main",
                    status: .acquiring,
                    message: "Ajoutez dans Music.app"
                ),
            ],
            phase: .waitingForManualAcquisition,
            historySessionID: "hist-1",
            importSessionID: "bridge-session-1",
            manualToken: "token",
            manualArtist: "Artist",
            manualTitle: "Title",
            manualInstructions: "instructions",
            manualCatalogURL: "https://music.apple.com/song/1"
        )

        viewModel.restoreManualAcquisition(from: report, generation: nil, historySessionID: "hist-1")

        XCTAssertEqual(viewModel.screenState, .waitingForManualAcquisition)
        XCTAssertEqual(viewModel.manualPrompt?.artist, "Artist")
        let pollStatus = viewModel.manualPollStatus
        XCTAssertTrue(pollStatus.contains("historique"))
    }

    func testImportResultCanResumeManualAcquisitionFlag() throws {
        let payload: BridgeJSONObject = [
            "import": .object([
                "playlist_name": .string("Demo"),
                "phase": .string("waiting_for_manual_acquisition"),
                "import_session_id": .string("bridge-session-1"),
                "manual_artist": .string("Artist"),
                "manual_title": .string("Title"),
                "outcomes": .array([]),
            ]),
        ]
        let result = try BridgePayloadBuilder.importResult(from: payload)
        XCTAssertTrue(result.canResumeManualAcquisition)
        XCTAssertNotNil(result.manualPrompt)
    }

    func testConfirmManualAcquisitionProbesBeforeContinue() async {
        final class ProbeFirstService: PlaylistImportServing {
            private(set) var probeCount = 0
            private(set) var continueCount = 0

            func importPlaylist(
                _ result: PlaylistGenerationResult,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                ImportResultState(playlistName: result.playlistName, phase: .completed)
            }

            func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
                continueCount += 1
                return ImportResultState(playlistName: "Demo", phase: .completed)
            }

            func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
                probeCount += 1
                return ManualAcquisitionProbeResult(
                    found: true,
                    message: "Morceau détecté dans la bibliothèque Music.app.",
                    diagnostics: ManualAcquisitionProbeDiagnostics(
                        importSessionID: importSessionID,
                        checkpointPath: "/tmp/checkpoint.json",
                        checkpointExists: true,
                        searchTerms: ["Artist Title"],
                        providerID: "apple_music"
                    )
                )
            }
        }

        let service = ProbeFirstService()
        let viewModel = ImportViewModel(service: service)
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

        XCTAssertEqual(service.probeCount, 1)
        XCTAssertEqual(service.continueCount, 1)
        XCTAssertEqual(viewModel.screenState, .report)
        XCTAssertNotNil(viewModel.architectManualDiagnostics)
    }

    func testConfirmManualAcquisitionDoesNotContinueWhenTrackMissing() async {
        final class MissingTrackService: PlaylistImportServing {
            private(set) var continueCount = 0

            func importPlaylist(
                _ result: PlaylistGenerationResult,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                ImportResultState(playlistName: result.playlistName, phase: .completed)
            }

            func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
                continueCount += 1
                return ImportResultState(playlistName: "Demo", phase: .completed)
            }

            func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
                ManualAcquisitionProbeResult(
                    found: false,
                    message: "Morceau pas encore détecté dans la bibliothèque. Vérifiez qu'il a bien été ajouté dans Music.app, puis réessayez.",
                    errorCode: "track_not_found"
                )
            }
        }

        let viewModel = ImportViewModel(service: MissingTrackService())
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

        XCTAssertEqual(viewModel.screenState, .waitingForManualAcquisition)
        let pollStatus = viewModel.manualPollStatus
        XCTAssertTrue(pollStatus.contains("pas encore détecté"))
    }

    func testConfirmManualAcquisitionIgnoresDuplicateClicks() async {
        final class SlowContinueService: PlaylistImportServing {
            private(set) var probeCount = 0
            private(set) var continueCount = 0

            func importPlaylist(
                _ result: PlaylistGenerationResult,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                ImportResultState(playlistName: result.playlistName, phase: .completed)
            }

            func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
                continueCount += 1
                try await Task.sleep(nanoseconds: 200_000_000)
                return ImportResultState(playlistName: "Demo", phase: .completed)
            }

            func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
                probeCount += 1
                try await Task.sleep(nanoseconds: 200_000_000)
                return ManualAcquisitionProbeResult(found: true, message: "ok")
            }
        }

        let service = SlowContinueService()
        let viewModel = ImportViewModel(service: service)
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

        async let first: Void = viewModel.confirmManualAcquisition()
        await Task.yield()
        let isContinuing = viewModel.isContinuingManual
        XCTAssertTrue(isContinuing)
        await viewModel.confirmManualAcquisition()
        await first

        XCTAssertEqual(service.probeCount, 1)
        XCTAssertEqual(service.continueCount, 0)
        XCTAssertEqual(viewModel.screenState, .waitingForManualAcquisition)
        XCTAssertTrue(viewModel.isContinuingManual)
    }

    func testResumeImportAfterPositiveProbeWhenCoordinatorBusy() async {
        final class ContinueOnResumeService: PlaylistImportServing {
            private(set) var continueCount = 0

            func importPlaylist(
                _ result: PlaylistGenerationResult,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                ImportResultState(playlistName: result.playlistName, phase: .completed)
            }

            func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
                continueCount += 1
                return ImportResultState(
                    playlistName: "Demo",
                    outcomes: [
                        ImportTrackOutcome(
                            artist: "Artist",
                            title: "Title",
                            section: "Main",
                            status: .added
                        ),
                    ],
                    phase: .completed
                )
            }

            func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
                ManualAcquisitionProbeResult(found: false)
            }
        }

        let service = ContinueOnResumeService()
        let viewModel = ImportViewModel(service: service)
        viewModel.restoreManualAcquisition(
            from: ImportResultState(
                playlistName: "Demo",
                outcomes: [],
                phase: .waitingForManualAcquisition,
                importSessionID: "session-auto",
                manualArtist: "Artist",
                manualTitle: "Title"
            ),
            generation: nil
        )

        // Simulates the path taken after applyProbeResult(found: true, userInitiated: false).
        await viewModel.resumeImportAfterPositiveProbe(importSessionID: "session-auto", token: nil)

        XCTAssertEqual(service.continueCount, 1)
        XCTAssertEqual(viewModel.screenState, .report)
    }

    func testLateBridgeEventsIgnoredAfterTerminalFinishImport() async {
        final class LateEventContinueService: PlaylistImportServing {
            func importPlaylist(
                _ result: PlaylistGenerationResult,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                ImportResultState(playlistName: result.playlistName, phase: .completed)
            }

            func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
                try await continueManualAcquisition(importSessionID: importSessionID, onEvent: { _ in })
            }

            func continueManualAcquisition(
                importSessionID: String,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                let result = ImportResultState(
                    playlistName: "Demo",
                    outcomes: [
                        ImportTrackOutcome(
                            artist: "Artist",
                            title: "Title",
                            section: "Main",
                            status: .added
                        ),
                    ],
                    phase: .partialSuccess
                )
                Task { @MainActor in
                    onEvent(
                        BridgeEventMessage(
                            id: "late-error",
                            event: .error,
                            payload: ["message": .string("Erreur bridge tardive")]
                        )
                    )
                    onEvent(
                        BridgeEventMessage(
                            id: "late-manual",
                            event: .manualAcquisitionRequired,
                            payload: [
                                "import_session_id": .string(importSessionID),
                                "artist": .string("Artist"),
                                "title": .string("Title"),
                            ]
                        )
                    )
                    onEvent(
                        BridgeEventMessage(
                            id: "late-progress",
                            event: .progress,
                            payload: ["phase": .string(ImportPhase.resolving.rawValue)]
                        )
                    )
                }
                return result
            }

            func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
                ManualAcquisitionProbeResult(found: false)
            }
        }

        let viewModel = ImportViewModel(service: LateEventContinueService())
        viewModel.restoreManualAcquisition(
            from: ImportResultState(
                playlistName: "Demo",
                outcomes: [],
                phase: .waitingForManualAcquisition,
                importSessionID: "session-late",
                manualArtist: "Artist",
                manualTitle: "Title"
            ),
            generation: nil
        )

        await viewModel.resumeImportAfterPositiveProbe(importSessionID: "session-late", token: nil)

        XCTAssertEqual(viewModel.screenState, .report)
        XCTAssertEqual(viewModel.report?.phase, .partialSuccess)
        let reportStep = viewModel.progress.currentStep

        for _ in 0..<12 {
            await Task.yield()
        }

        XCTAssertEqual(viewModel.screenState, .report)
        XCTAssertEqual(viewModel.report?.phase, .partialSuccess)
        XCTAssertEqual(viewModel.progress.currentStep, reportStep)
    }

    func testLiveRetryFromPartialSuccessReportPreservesExistingOutcomes() async {
        let initialOutcomes = [
            ImportTrackOutcome(artist: "Motörhead", title: "Ace of Spades", section: "Main", status: .added),
            ImportTrackOutcome(
                artist: "Motörhead",
                title: "Motörhead",
                section: "Main",
                status: .notFound,
                message: "Morceau confirmé en bibliothèque."
            ),
            ImportTrackOutcome(artist: "Metallica", title: "Nothing Else Matters", section: "Main", status: .notFound),
        ]

        final class LiveRetryService: PlaylistImportServing {
            private let seedOutcomes: [ImportTrackOutcome]
            private(set) var receivedExistingOutcomes: [ImportTrackOutcome]?

            init(seedOutcomes: [ImportTrackOutcome]) {
                self.seedOutcomes = seedOutcomes
            }

            func importPlaylist(
                _ result: PlaylistGenerationResult,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                ImportResultState(
                    playlistName: result.playlistName,
                    outcomes: seedOutcomes,
                    phase: .partialSuccess,
                    historySessionID: result.historySessionID
                )
            }

            func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
                ImportResultState(playlistName: "Demo", phase: .completed)
            }

            func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
                ManualAcquisitionProbeResult(found: false)
            }

            func retryImportTracks(
                _ generationResult: PlaylistGenerationResult,
                trackIndices: [Int],
                existingOutcomes: [ImportTrackOutcome]?,
                historySessionID: String?,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                receivedExistingOutcomes = existingOutcomes
                var updated = existingOutcomes ?? []
                if let index = trackIndices.first, index < updated.count {
                    updated[index] = ImportTrackOutcome(
                        artist: updated[index].artist,
                        title: updated[index].title,
                        section: updated[index].section,
                        status: .added,
                        message: "Ajouté"
                    )
                }
                return ImportResultState(
                    playlistName: generationResult.playlistName,
                    outcomes: updated,
                    phase: .partialSuccess,
                    historySessionID: historySessionID ?? generationResult.historySessionID
                )
            }
        }

        let service = LiveRetryService(seedOutcomes: initialOutcomes)
        let viewModel = ImportViewModel(service: service)
        let generation = PlaylistGenerationResult(
            playlistName: "3e test",
            sections: [
                GeneratedSectionPreview(
                    name: "Main",
                    tracks: initialOutcomes.map {
                        GeneratedTrackPreview(
                            artist: $0.artist,
                            title: $0.title,
                            section: $0.section,
                            score: 80,
                            confidence: .high,
                            source: "test"
                        )
                    }
                ),
            ],
            averageScore: 0.8,
            providerID: .appleMusic,
            historySessionID: "hist-live-retry"
        )

        await viewModel.importPlaylist(generation)
        XCTAssertEqual(viewModel.screenState, .report)

        await viewModel.retryImportTrack(at: 1)

        XCTAssertEqual(viewModel.screenState, .report)
        XCTAssertEqual(service.receivedExistingOutcomes?.count, initialOutcomes.count)
        XCTAssertEqual(viewModel.report?.outcomes[0].status, .added)
        XCTAssertEqual(viewModel.report?.outcomes[1].status, .added)
        XCTAssertEqual(viewModel.report?.outcomes[2].status, .notFound)
    }

    func testLateBridgeEventsIgnoredDuringLiveRetryFromReport() async {
        let initialOutcomes = [
            ImportTrackOutcome(artist: "Artist A", title: "Track A", section: "Main", status: .added),
            ImportTrackOutcome(artist: "Artist B", title: "Track B", section: "Main", status: .notFound),
        ]

        final class LateEventRetryService: PlaylistImportServing {
            private let seedOutcomes: [ImportTrackOutcome]

            init(seedOutcomes: [ImportTrackOutcome]) {
                self.seedOutcomes = seedOutcomes
            }

            func importPlaylist(
                _ result: PlaylistGenerationResult,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                Task { @MainActor in
                    onEvent(
                        BridgeEventMessage(
                            id: "stale-manual",
                            event: .manualAcquisitionRequired,
                            payload: [
                                "import_session_id": .string("stale-session"),
                                "artist": .string("Artist B"),
                                "title": .string("Track B"),
                            ]
                        )
                    )
                }
                return ImportResultState(
                    playlistName: result.playlistName,
                    outcomes: seedOutcomes,
                    phase: .partialSuccess
                )
            }

            func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
                ImportResultState(playlistName: "Demo", phase: .completed)
            }

            func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
                ManualAcquisitionProbeResult(found: false)
            }

            func retryImportTracks(
                _ generationResult: PlaylistGenerationResult,
                trackIndices: [Int],
                existingOutcomes: [ImportTrackOutcome]?,
                historySessionID: String?,
                onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
            ) async throws -> ImportResultState {
                ImportResultState(
                    playlistName: generationResult.playlistName,
                    outcomes: existingOutcomes ?? [],
                    phase: .partialSuccess
                )
            }
        }

        let viewModel = ImportViewModel(service: LateEventRetryService(seedOutcomes: initialOutcomes))
        let generation = PlaylistGenerationResult(
            playlistName: "Retry Late Events",
            sections: [
                GeneratedSectionPreview(
                    name: "Main",
                    tracks: initialOutcomes.map {
                        GeneratedTrackPreview(
                            artist: $0.artist,
                            title: $0.title,
                            section: $0.section,
                            score: 80,
                            confidence: .high,
                            source: "test"
                        )
                    }
                ),
            ],
            averageScore: 0.8,
            providerID: .appleMusic
        )

        await viewModel.importPlaylist(generation)
        XCTAssertEqual(viewModel.screenState, .report)
        let reportPhase = viewModel.report?.phase

        await viewModel.retryImportTrack(at: 1)

        for _ in 0..<12 {
            await Task.yield()
        }

        XCTAssertEqual(viewModel.screenState, .report)
        XCTAssertEqual(viewModel.report?.phase, reportPhase)
    }
}
