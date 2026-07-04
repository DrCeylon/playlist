import Foundation
import ResonanceCore
@testable import ResonanceMac
import XCTest

actor MockBridgeTransport: BridgeTransport {
    private(set) var lastCommand: BridgeCommand?
    private let responseHandler: @Sendable (BridgeCommand, BridgeJSONObject) -> (
        BridgeResponseMessage,
        [BridgeEventMessage]
    )

    init(
        responseHandler: @escaping @Sendable (BridgeCommand, BridgeJSONObject) -> (
            BridgeResponseMessage,
            [BridgeEventMessage]
        )
    ) {
        self.responseHandler = responseHandler
    }

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
        _ = requestID
        _ = onEvent
        _ = onDiagnostic
        lastCommand = command
        return responseHandler(command, params)
    }
}

final class BridgeClientTests: XCTestCase {
    func testPythonEngineBridgeServiceGenerateUsesTransport() async throws {
        let transport = MockBridgeTransport { command, _ in
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
        XCTAssertEqual(await transport.lastCommand, .generatePlaylist)
    }
}
