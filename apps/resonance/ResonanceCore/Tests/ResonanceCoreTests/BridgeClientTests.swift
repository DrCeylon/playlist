import Foundation
@testable import ResonanceCore
import XCTest

final class BridgeClientTests: XCTestCase {
    func testBridgeCommandRawValuesMatchPythonContract() {
        XCTAssertEqual(BridgeCommand.generatePlaylist.rawValue, "generate_playlist")
        XCTAssertEqual(BridgeCommand.importPlaylist.rawValue, "import_playlist")
        XCTAssertEqual(BridgeCommand.diagnostics.rawValue, "diagnostics")
        XCTAssertEqual(BridgeCommand.continueManualAcquisition.rawValue, "continue_manual_acquisition")
        XCTAssertEqual(BridgeCommand.listHistory.rawValue, "list_history")
        XCTAssertEqual(BridgeCommand.getHistorySession.rawValue, "get_history_session")
        XCTAssertEqual(BridgeCommand.autocompleteSearch.rawValue, "autocomplete_search")
        XCTAssertEqual(BridgeCommand.listManagedPlaylists.rawValue, "list_managed_playlists")
        XCTAssertEqual(BridgeCommand.getManagedPlaylist.rawValue, "get_managed_playlist")
        XCTAssertEqual(BridgeCommand.syncManagedPlaylist.rawValue, "sync_managed_playlist")
        XCTAssertEqual(BridgeCommand.planSync.rawValue, "plan_sync")
        XCTAssertEqual(BridgeCommand.listRemotePlaylists.rawValue, "list_remote_playlists")
        XCTAssertEqual(BridgeCommand.getRemotePlaylist.rawValue, "get_remote_playlist")
        XCTAssertEqual(BridgeCommand.importRemotePlaylist.rawValue, "import_remote_playlist")
        XCTAssertEqual(BridgeCommand.applySync.rawValue, "apply_sync")
        XCTAssertEqual(BridgeCommand.providerAuthStatus.rawValue, "provider_auth_status")
        XCTAssertEqual(BridgeCommand.providerConnect.rawValue, "provider_connect")
        XCTAssertEqual(BridgeCommand.providerDisconnect.rawValue, "provider_disconnect")
        XCTAssertEqual(BridgeCommand.loadRemotePlaylistFromFile.rawValue, "load_remote_playlist_from_file")
    }

    func testDiagnosticsSnapshotDecoding() throws {
        let payload: BridgeJSONObject = [
            "engine_version": .string("1.0.0"),
            "summary": .object([
                "bridge_status": .string("connected"),
                "platform": .string("darwin"),
                "execution_ms": .number(8),
                "catalog_cache_entries": .number(3),
                "identity_cache_entries": .number(1),
                "catalog_cache_enabled": .bool(true),
                "country_code": .string("fr"),
                "active_providers": .array([
                    .object([
                        "provider_id": .string("apple_music"),
                        "display_name": .string("Apple Music"),
                        "is_available": .bool(true),
                        "is_connected": .bool(true),
                        "unavailable_reason": .string(""),
                    ]),
                ]),
                "recent_reports": .array([]),
                "reports_directory": .string("reports"),
            ]),
            "events": .array([
                .object([
                    "phase": .string("bridge"),
                    "message": .string("Connecté"),
                    "level": .string("info"),
                    "timestamp_iso": .string("2026-01-01T00:00:00"),
                    "payload": .array([.array([.string("bridge_status"), .string("connected")])]),
                ]),
            ]),
        ]
        let snapshot = try BridgePayloadBuilder.diagnosticsSnapshot(from: payload)
        XCTAssertEqual(snapshot.engineVersion, "1.0.0")
        XCTAssertEqual(snapshot.summary.catalogCacheEntries, 3)
        XCTAssertEqual(snapshot.events.count, 1)
        XCTAssertEqual(snapshot.events[0].payload.first?.key, "bridge_status")
    }

    func testDiagnosticsSnapshotToleratesMissingSummary() throws {
        let payload: BridgeJSONObject = [
            "engine_version": .string("1.0.0"),
            "events": .array([]),
        ]
        let snapshot = try BridgePayloadBuilder.diagnosticsSnapshot(from: payload)
        XCTAssertEqual(snapshot.engineVersion, "1.0.0")
        XCTAssertEqual(snapshot.summary.bridgeStatus, "unknown")
    }

    func testHistorySessionDecoding() {
        let payload: BridgeJSONObject = [
            "sessions": .array([
                .object([
                    "session_id": .string("hist-1"),
                    "started_at_iso": .string("2026-07-02T08:00:00"),
                    "finished_at_iso": .string("2026-07-02T08:01:00"),
                    "playlist_name": .string("Demo"),
                    "provider_id": .string("apple_music"),
                    "status": .string("generated"),
                    "track_count": .number(5),
                    "added_count": .number(0),
                    "skipped_count": .number(0),
                    "not_found_count": .number(0),
                    "error_count": .number(0),
                    "duration_ms": .number(1000),
                    "text_report_path": .string(""),
                    "json_report_path": .string(""),
                ]),
            ]),
        ]
        let sessions = BridgePayloadBuilder.historySessions(from: payload)
        XCTAssertEqual(sessions.count, 1)
        XCTAssertEqual(sessions.first?.sessionID, "hist-1")
    }

    func testBridgeResponseParserDecodesSuccess() throws {
        let line = """
        {"id":"1","type":"response","ok":true,"result":{"generation":{"playlist_name":"Demo","sections":[],"average_score":0.8,"provider_id":"apple_music"}}}
        """
        let response = try BridgeResponseParser.parseResponseLine(line)
        XCTAssertTrue(response.ok)
        XCTAssertNotNil(response.result["generation"]?.objectValue)
    }

    func testParseConversationCollectsProgressEvent() throws {
        let requestID = "req-1"
        let eventLine = """
        {"id":"\(requestID)","type":"event","event":"progress","payload":{"phase":"resolving","total_tracks":3,"processed_tracks":1}}
        """
        let responseLine = """
        {"id":"\(requestID)","type":"response","ok":true,"result":{"import":{"playlist_name":"Demo","phase":"completed","outcomes":[]}}}
        """
        let parsed = try BridgeClient.parseConversation(
            requestID: requestID,
            lines: [eventLine, responseLine]
        )
        XCTAssertEqual(parsed.events.count, 1)
        XCTAssertEqual(parsed.events.first?.event, .progress)
        XCTAssertEqual(parsed.events.first?.payload["total_tracks"]?.intValue, 3)
    }

    func testDispatchStreamingLineInvokesProgressCallback() {
        let line = """
        {"id":"req-1","type":"event","event":"progress","payload":{"phase":"resolving","total_tracks":3,"processed_tracks":1}}
        """
        let received = LockedBox<BridgeEventMessage?>(nil)
        BridgeClient.dispatchStreamingLine(
            line: line,
            requestID: "req-1",
            onEvent: { event in
                received.withLock { $0 = event }
            },
            onDiagnostic: nil
        )
        XCTAssertEqual(received.value?.event, .progress)
        XCTAssertEqual(received.value?.payload["total_tracks"]?.intValue, 3)
    }

    func testGenerationRequestDictionaryUsesSnakeCase() {
        let request = PlaylistGenerationRequest(
            name: "Pool",
            providerID: .appleMusic,
            seeds: [SeedReference(artist: "Kygo", title: "Firestone")],
            targetTrackCount: 12
        )
        let payload = BridgeContracts.generationRequestDictionary(request)
        XCTAssertEqual(payload["provider_id"]?.stringValue, "apple_music")
        XCTAssertEqual(payload["target_track_count"]?.intValue, 12)
    }

    func testParseConversationIgnoresNonJSONStdoutLines() throws {
        let requestID = "req-import-1"
        let eventLine = """
        {"id":"\(requestID)","type":"event","event":"progress","payload":{"phase":"resolving","processed_tracks":2,"total_tracks":5}}
        """
        let noiseLine = "resonance-import: resolve 3/5: Artist — Title"
        let responseLine = """
        {"id":"\(requestID)","type":"response","ok":true,"result":{"import":{"playlist_name":"Demo","phase":"partial_success","outcomes":[]}}}
        """
        let parsed = try BridgeClient.parseConversation(
            requestID: requestID,
            lines: [eventLine, noiseLine, responseLine]
        )
        XCTAssertTrue(parsed.response.ok)
        XCTAssertEqual(parsed.events.count, 1)
        XCTAssertEqual(parsed.events.first?.event, .progress)
    }

    func testParseConversationFailsWhenResponseMissing() {
        let requestID = "req-import-2"
        XCTAssertThrowsError(
            try BridgeClient.parseConversation(
                requestID: requestID,
                lines: ["not json at all", "still not json"]
            )
        ) { error in
            XCTAssertEqual(error as? BridgeClientError, .invalidResponse)
        }
    }

    func testParseConversationDecodesPartialSuccessImport() throws {
        let requestID = "req-import-3"
        let responseLine = """
        {"id":"\(requestID)","type":"response","ok":true,"result":{"import":{"playlist_name":"Demo","phase":"partial_success","outcomes":[{"artist":"A","title":"B","section":"Main","status":"not_found","message":"Introuvable"}]}}}
        """
        let parsed = try BridgeClient.parseConversation(requestID: requestID, lines: [responseLine])
        let importState = try BridgePayloadBuilder.importResult(from: parsed.response.result)
        XCTAssertEqual(importState.phase, .partialSuccess)
        XCTAssertEqual(importState.notFoundCount, 1)
    }

    func testParseConversationDecodesFailedImportWithBridgeError() {
        let requestID = "req-import-4"
        let responseLine = """
        {"id":"\(requestID)","type":"response","ok":false,"result":{},"error":{"code":"provider_unavailable","message":"Music.app inaccessible"}}
        """
        XCTAssertThrowsError(
            try BridgeClient.parseConversation(requestID: requestID, lines: [responseLine])
        ) { error in
            guard case .bridge(let payload) = error as? BridgeClientError else {
                return XCTFail("Expected bridge error")
            }
            XCTAssertEqual(payload.code, .providerUnavailable)
            XCTAssertTrue(payload.message.contains("Music.app"))
        }
    }

    func testDispatchStreamingLineIgnoresNonJSONStdout() {
        let eventCount = LockedBox(0)
        let diagnosticCount = LockedBox(0)
        BridgeClient.dispatchStreamingLine(
            line: "resonance-bridge: human log on stdout by mistake",
            requestID: "req-1",
            onEvent: { _ in eventCount.increment() },
            onDiagnostic: { _ in diagnosticCount.increment() }
        )
        XCTAssertEqual(eventCount.value, 0)
        XCTAssertEqual(diagnosticCount.value, 0)
    }

    func testBridgePayloadBuilderImportResult() throws {
        let payload: BridgeJSONObject = [
            "import": .object([
                "playlist_name": .string("Demo"),
                "phase": .string("completed"),
                "outcomes": .array([
                    .object([
                        "artist": .string("Kygo"),
                        "title": .string("Firestone"),
                        "section": .string("Main"),
                        "status": .string("added"),
                        "message": .string(""),
                    ]),
                ]),
            ]),
        ]
        let result = try BridgePayloadBuilder.importResult(from: payload)
        XCTAssertEqual(result.addedCount, 1)
        XCTAssertEqual(result.phase, .completed)
    }
}
