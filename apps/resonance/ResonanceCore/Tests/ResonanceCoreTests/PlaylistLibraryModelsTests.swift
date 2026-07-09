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
