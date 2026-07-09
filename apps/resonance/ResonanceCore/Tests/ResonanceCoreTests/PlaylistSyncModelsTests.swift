import ResonanceCore
import XCTest

final class PlaylistSyncModelsTests: XCTestCase {
    func testPlaylistSyncPlanDecoding() {
        let payload: BridgeJSONObject = [
            "sync_plan": .object([
                "local_playlist_id": .string("local-1"),
                "target_provider_id": .string("spotify"),
                "direction": .string("pull_from_provider"),
                "sync_mode": .string("dry_run"),
                "remote_playlist_id": .string("remote-1"),
                "playlist_name_local": .string("Local"),
                "playlist_name_remote": .string("Remote"),
                "actions": .array([
                    .object([
                        "kind": .string("add_track"),
                        "track_key": .string("kygo::firestone"),
                        "artist": .string("Kygo"),
                        "title": .string("Firestone"),
                        "message": .string("Ajouter"),
                    ]),
                ]),
                "conflicts": .array([]),
                "summary": .object([
                    "additions": .number(1),
                    "removals": .number(0),
                    "already_present": .number(0),
                    "metadata_mismatches": .number(0),
                    "reorders": .number(0),
                    "conflicts": .number(0),
                    "rename_required": .bool(false),
                ]),
            ]),
        ]
        let plan = BridgePayloadBuilder.playlistSyncPlan(from: payload)
        XCTAssertEqual(plan?.syncMode, .dryRun)
        XCTAssertEqual(plan?.summary.additions, 1)
        XCTAssertEqual(plan?.actions.first?.kind, .addTrack)
    }
}
