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
        XCTAssertEqual(playlists[0].linkedRemoteRefs[0].lastSeenSnapshotChecksum, "abc123")
    }

    func testLinkedRemoteRefLegacyChecksumMigration() {
        let payload: BridgeJSONObject = [
            "playlists": .array([
                .object([
                    "local_playlist_id": .string("mpl-legacy"),
                    "name": .string("Legacy"),
                    "provider_id": .string("apple_music"),
                    "track_count": .number(1),
                    "sync_status": .string("synced"),
                    "linked_remote_refs": .array([
                        .object([
                            "provider_id": .string("apple_music"),
                            "remote_playlist_id": .string("remote-1"),
                            "snapshot_checksum": .string("legacy-checksum"),
                        ]),
                    ]),
                ]),
            ]),
        ]
        let playlists = BridgePayloadBuilder.managedPlaylists(from: payload)
        XCTAssertEqual(playlists[0].linkedRemoteRefs[0].lastSeenSnapshotChecksum, "legacy-checksum")
        XCTAssertEqual(playlists[0].linkedRemoteRefs[0].lastAppliedSnapshotChecksum, "")
    }

    func testPlaylistSyncApplyResultDecoding() {
        let payload: BridgeJSONObject = [
            "sync_apply": .object([
                "final_sync_status": .string("synced"),
                "message": .string("ok"),
                "requires_confirmation": .bool(false),
                "operation": .object([
                    "operation_id": .string("syncop-1"),
                    "status": .string("completed"),
                    "local_playlist_version_before": .number(1),
                    "local_playlist_version_after": .number(1),
                ]),
                "actions_applied": .array([]),
            ]),
        ]
        let result = BridgePayloadBuilder.playlistSyncApplyResult(from: payload)
        XCTAssertEqual(result?.operation.status, .completed)
        XCTAssertEqual(result?.message, "ok")
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
