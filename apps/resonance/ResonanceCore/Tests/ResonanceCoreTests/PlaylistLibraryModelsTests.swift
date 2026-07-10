import ResonanceCore
import XCTest

final class PlaylistLibraryModelsTests: XCTestCase {
    func testManagedPlaylistDecoding() {
        let payload: BridgeJSONObject = [
            "playlists": .array([
                .object([
                    "local_playlist_id": .string("hist-1"),
                    "name": .string("Demo"),
                    "provider_id": .string("apple_music"),
                    "track_count": .number(5),
                    "sync_status": .string("synced"),
                    "source_kind": .string("generated_import"),
                    "history_session_id": .string("1"),
                ]),
            ]),
        ]
        let playlists = BridgePayloadBuilder.managedPlaylists(from: payload)
        XCTAssertEqual(playlists.count, 1)
        XCTAssertEqual(playlists[0].name, "Demo")
        XCTAssertEqual(playlists[0].providerID, .appleMusic)
        XCTAssertEqual(playlists[0].origin, .generated)
        XCTAssertEqual(playlists[0].playlistVersion, 1)
    }

    func testManagedPlaylistDecodingWithRepositoryFields() {
        let payload: BridgeJSONObject = [
            "playlists": .array([
                .object([
                    "local_playlist_id": .string("mpl-1"),
                    "name": .string("Demo"),
                    "provider_id": .string("apple_music"),
                    "track_count": .number(5),
                    "sync_status": .string("synced"),
                    "source_kind": .string("provider_library"),
                    "origin": .string("provider_library"),
                    "playlist_version": .number(2),
                    "linked_remote_refs": .array([
                        .object([
                            "provider_id": .string("apple_music"),
                            "remote_playlist_id": .string("remote-1"),
                            "snapshot_checksum": .string("abc123"),
                            "sync_state": .string("linked"),
                            "last_sync_at": .string("2026-07-10T10:00:00"),
                        ]),
                    ]),
                    "created_at_iso": .string("2026-07-10T09:00:00"),
                    "updated_at_iso": .string("2026-07-10T10:00:00"),
                ]),
            ]),
        ]
        let playlists = BridgePayloadBuilder.managedPlaylists(from: payload)
        XCTAssertEqual(playlists.count, 1)
        XCTAssertEqual(playlists[0].origin, .providerLibrary)
        XCTAssertEqual(playlists[0].playlistVersion, 2)
        XCTAssertEqual(playlists[0].linkedRemoteRefs.count, 1)
        XCTAssertEqual(playlists[0].linkedRemoteRefs[0].snapshotChecksum, "abc123")
    }

    func testPlaylistSyncResultDecoding() {
        let payload: BridgeJSONObject = [
            "sync": .object([
                "local_playlist_id": .string("hist-1"),
                "sync_status": .string("pending"),
                "message": .string("queued"),
                "conflicts": .array([]),
            ]),
        ]
        let result = BridgePayloadBuilder.playlistSyncResult(from: payload)
        XCTAssertEqual(result?.syncStatus, .pending)
        XCTAssertEqual(result?.message, "queued")
    }
}
