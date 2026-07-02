import Foundation
import ResonanceCore
@testable import ResonanceMac

final class MockBridgeTransport: BridgeTransport, @unchecked Sendable {
    var lastCommand: BridgeCommand?
    var handler: ((BridgeCommand, BridgeJSONObject) -> (BridgeResponseMessage, [BridgeEventMessage]))?

    func send(
        command: BridgeCommand,
        requestID: String,
        params: BridgeJSONObject,
        onEvent: (@Sendable (BridgeEventMessage) -> Void)?,
        onDiagnostic: (@Sendable (String) -> Void)?
    ) async throws -> (
        response: BridgeResponseMessage,
        events: [BridgeEventMessage]
    ) {
        _ = onEvent
        _ = onDiagnostic
        lastCommand = command
        if let handler {
            return handler(command, params)
        }
        throw BridgeClientError.bridgeUnavailable
    }
}

import XCTest

final class BridgeClientTests: XCTestCase {
    func testBridgeCommandRawValuesMatchPythonContract() {
        XCTAssertEqual(BridgeCommand.generatePlaylist.rawValue, "generate_playlist")
        XCTAssertEqual(BridgeCommand.importPlaylist.rawValue, "import_playlist")
        XCTAssertEqual(BridgeCommand.diagnostics.rawValue, "diagnostics")
        XCTAssertEqual(BridgeCommand.continueManualAcquisition.rawValue, "continue_manual_acquisition")
        XCTAssertEqual(BridgeCommand.listHistory.rawValue, "list_history")
        XCTAssertEqual(BridgeCommand.getHistorySession.rawValue, "get_history_session")
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

    func testDispatchStreamingEventParsesProgressEvent() {
        let line = """
        {"id":"req-1","type":"event","event":"progress","payload":{"phase":"resolving","total_tracks":3,"processed_tracks":1}}
        """
        var received: BridgeEventMessage?
        BridgeClient.dispatchStreamingEvent(line: line) { event in
            received = event
        }
        XCTAssertEqual(received?.event, .progress)
        XCTAssertEqual(received?.payload["total_tracks"]?.intValue, 3)
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

    func testPythonEngineBridgeServiceGenerateUsesTransport() async throws {
        let transport = MockBridgeTransport()
        transport.handler = { command, _ in
            XCTAssertEqual(command, .generatePlaylist)
            let result: BridgeJSONObject = [
                "generation": .object([
                    "playlist_name": .string("Demo"),
                    "sections": .array([
                        .object([
                            "name": .string("Main"),
                            "tracks": .array([
                                .object([
                                    "artist": .string("Kygo"),
                                    "title": .string("Firestone"),
                                    "section": .string("Main"),
                                    "score": .number(0.91),
                                    "confidence": .string("high"),
                                    "source": .string("seed"),
                                ]),
                            ]),
                        ]),
                    ]),
                    "average_score": .number(0.91),
                    "provider_id": .string("apple_music"),
                ]),
            ]
            return (
                BridgeResponseMessage(id: "1", ok: true, result: result, error: nil),
                []
            )
        }
        let service = PythonEngineBridgeService(configuration: nil, transport: transport)
        let result = try await service.generate(
            request: PlaylistGenerationRequest(
                name: "Demo",
                providerID: .appleMusic,
                seeds: [SeedReference(artist: "Kygo", title: "Firestone")],
                targetTrackCount: 5
            )
        )
        XCTAssertEqual(result.playlistName, "Demo")
        XCTAssertEqual(result.trackCount, 1)
    }
}
