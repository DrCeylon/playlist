import ResonanceCore
import XCTest

final class RemotePlaylistBridgeTests: XCTestCase {
    func testRemotePlaylistBridgePayloadRoundTrip() {
        let listPayload: BridgeJSONObject = [
            "remote_playlists": .array([
                .object([
                    "provider_id": .string("apple_music"),
                    "remote_playlist_id": .string("pl-42"),
                    "name": .string("Workout"),
                    "track_count": .number(1),
                    "snapshot_at_iso": .string("2026-07-09T12:00:00Z"),
                ]),
            ]),
        ]
        let playlists = BridgePayloadBuilder.remotePlaylists(from: listPayload)
        XCTAssertEqual(playlists.first?.remotePlaylistID, "pl-42")

        let detailPayload: BridgeJSONObject = [
            "remote_playlist": .object([
                "provider_id": .string("apple_music"),
                "remote_playlist_id": .string("pl-42"),
                "name": .string("Workout"),
                "snapshot_at_iso": .string("2026-07-09T12:00:00Z"),
                "track_count": .number(1),
                "checksum": .string("abc123"),
                "source_kind": .string("provider_library"),
                "tracks": .array([
                    .object([
                        "remote_track_id": .string("t-1"),
                        "artist": .string("Kygo"),
                        "title": .string("Firestone"),
                        "position": .number(1),
                    ]),
                ]),
            ]),
        ]
        let snapshot = BridgePayloadBuilder.remotePlaylistSnapshot(from: detailPayload)
        XCTAssertEqual(snapshot?.tracks.first?.title, "Firestone")
    }
}
