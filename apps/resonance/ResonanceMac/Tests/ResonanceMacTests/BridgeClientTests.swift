import Foundation
import ResonanceCore
@testable import ResonanceMac

final class MockBridgeTransport: BridgeTransport, @unchecked Sendable {
    var lastCommand: BridgeCommand?
    var handler: ((BridgeCommand, [String: Any]) -> (BridgeResponseMessage, [BridgeEventMessage]))?

    func send(command: BridgeCommand, requestID: String, params: [String: Any]) async throws -> (
        response: BridgeResponseMessage,
        events: [BridgeEventMessage]
    ) {
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
        XCTAssertEqual(BridgeCommand.continueManualAcquisition.rawValue, "continue_manual_acquisition")
    }

    func testBridgeResponseParserDecodesSuccess() throws {
        let line = """
        {"id":"1","type":"response","ok":true,"result":{"generation":{"playlist_name":"Demo","sections":[],"average_score":0.8,"provider_id":"apple_music"}}}
        """
        let response = try BridgeResponseParser.parseResponseLine(line)
        XCTAssertTrue(response.ok)
        XCTAssertEqual(response.result["generation"] as? [String: Any] != nil, true)
    }

    func testGenerationRequestDictionaryUsesSnakeCase() {
        let request = PlaylistGenerationRequest(
            name: "Pool",
            providerID: .appleMusic,
            seeds: [SeedReference(artist: "Kygo", title: "Firestone")],
            targetTrackCount: 12
        )
        let payload = BridgeContracts.generationRequestDictionary(request)
        XCTAssertEqual(payload["provider_id"] as? String, "apple_music")
        XCTAssertEqual(payload["target_track_count"] as? Int, 12)
    }

    func testBridgePayloadBuilderImportResult() throws {
        let payload: [String: Any] = [
            "import": [
                "playlist_name": "Demo",
                "phase": "completed",
                "outcomes": [
                    [
                        "artist": "Kygo",
                        "title": "Firestone",
                        "section": "Main",
                        "status": "added",
                        "message": "",
                    ],
                ],
            ],
        ]
        let result = try BridgePayloadBuilder.importResult(from: payload)
        XCTAssertEqual(result.addedCount, 1)
        XCTAssertEqual(result.phase, .completed)
    }

    func testPythonEngineBridgeServiceGenerateUsesTransport() async throws {
        let transport = MockBridgeTransport()
        transport.handler = { command, _ in
            XCTAssertEqual(command, .generatePlaylist)
            let result: [String: Any] = [
                "generation": [
                    "playlist_name": "Demo",
                    "sections": [
                        [
                            "name": "Main",
                            "tracks": [
                                [
                                    "artist": "Kygo",
                                    "title": "Firestone",
                                    "section": "Main",
                                    "score": 0.91,
                                    "confidence": "high",
                                    "source": "seed",
                                ],
                            ],
                        ],
                    ],
                    "average_score": 0.91,
                    "provider_id": "apple_music",
                ],
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
