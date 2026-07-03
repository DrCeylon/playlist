import Foundation
import ResonanceCore

public struct MockPlaylistImportService: PlaylistImportServing {
    public init() {}

    public func importPlaylist(
        _ result: PlaylistGenerationResult,
        onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
    ) async throws -> ImportResultState {
        onEvent(
            BridgeEventMessage(
                id: "mock-import",
                event: .progress,
                payload: [
                    "phase": .string(ImportPhase.resolving.rawValue),
                    "total_tracks": .number(Double(result.trackCount)),
                    "processed_tracks": .number(0),
                ]
            )
        )
        try await Task.sleep(nanoseconds: 250_000_000)
        let outcomes = result.sections.flatMap { section in
            section.tracks.map { track in
                ImportTrackOutcome(
                    artist: track.artist,
                    title: track.title,
                    section: section.name,
                    status: .added,
                    message: "mock"
                )
            }
        }
        onEvent(
            BridgeEventMessage(
                id: "mock-import",
                event: .completed,
                payload: ["added_count": .number(Double(outcomes.count))]
            )
        )
        return ImportResultState(
            playlistName: result.playlistName,
            outcomes: outcomes,
            phase: .completed
        )
    }

    public func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
        _ = importSessionID
        throw PlaylistImportError.bridgeUnavailable
    }

    public func probeManualAcquisition(importSessionID: String) async throws -> Bool {
        _ = importSessionID
        return false
    }
}
