import ResonanceCore
import XCTest

final class RemotePlaylistModelsTests: XCTestCase {
    func testRemotePlaylistDecoding() {
        let payload: BridgeJSONObject = [
            "remote_playlists": .array([
                .object([
                    "provider_id": .string("spotify"),
                    "remote_playlist_id": .string("pl-99"),
                    "name": .string("Chill"),
                    "track_count": .number(8),
                    "is_public": .bool(false),
                    "owner_label": .string("demo"),
                    "snapshot_at_iso": .string("2026-07-09T12:00:00Z"),
                ]),
            ]),
        ]
        let playlists = BridgePayloadBuilder.remotePlaylists(from: payload)
        XCTAssertEqual(playlists.count, 1)
        XCTAssertEqual(playlists[0].providerID, .spotify)
        XCTAssertEqual(playlists[0].remotePlaylistID, "pl-99")
        XCTAssertEqual(playlists[0].trackCount, 8)
    }

    func testRemotePlaylistSnapshotDecoding() {
        let payload: BridgeJSONObject = [
            "remote_playlist": .object([
                "provider_id": .string("apple_music"),
                "remote_playlist_id": .string("am-1"),
                "name": .string("Workout"),
                "snapshot_at_iso": .string("2026-07-09T12:00:00Z"),
                "track_count": .number(1),
                "checksum": .string("deadbeef"),
                "source_kind": .string("provider_library"),
                "tracks": .array([
                    .object([
                        "remote_track_id": .string("t1"),
                        "artist": .string("Kygo"),
                        "title": .string("Firestone"),
                        "album": .string("Cloud Nine"),
                        "duration_ms": .number(245000),
                        "position": .number(1),
                        "provider_metadata": .object([:]),
                    ]),
                ]),
            ]),
        ]
        let snapshot = BridgePayloadBuilder.remotePlaylistSnapshot(from: payload)
        XCTAssertEqual(snapshot?.providerID, .appleMusic)
        XCTAssertEqual(snapshot?.tracks.count, 1)
        XCTAssertEqual(snapshot?.tracks[0].artist, "Kygo")
        XCTAssertEqual(snapshot?.checksum, "deadbeef")
    }

    func testRemoteProviderAccountDecoding() {
        let payload: BridgeJSONObject = [
            "provider_accounts": .array([
                .object([
                    "provider_id": .string("youtube_music"),
                    "display_name": .string("YouTube Music"),
                    "auth_state": .string("experimental_unavailable"),
                    "last_connected_at_iso": .string(""),
                    "capabilities": .array([.string("experimental")]),
                ]),
            ]),
        ]
        let accounts = BridgePayloadBuilder.remoteProviderAccounts(from: payload)
        XCTAssertEqual(accounts.count, 1)
        XCTAssertEqual(accounts[0].authState, .experimentalUnavailable)
        XCTAssertEqual(accounts[0].capabilities, [.experimental])
    }

    func testProviderAuthStateDecoding() {
        let payload: BridgeJSONObject = [
            "auth_state": .string("connected"),
        ]
        XCTAssertEqual(BridgePayloadBuilder.providerAuthState(from: payload), .connected)
    }
}
