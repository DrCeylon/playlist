import ResonanceCore
import XCTest

/// Compile-time guard: shared bridge contracts must stay visible via `import ResonanceCore`.
private enum BridgeSymbolVisibilityGuard {
    static let transport: any BridgeTransport.Type = BridgeClient.self
    static let payloadBuilder = BridgePayloadBuilder.self
    static let clientError: BridgeClientError = .bridgeUnavailable
    static let errorPayload = BridgeErrorPayload(code: .invalidRequest, message: "guard")
}

final class BridgeSymbolVisibilityGuardTests: XCTestCase {
    func testSharedBridgeSymbolsAreVisibleFromResonanceCore() {
        XCTAssertTrue(BridgeSymbolVisibilityGuard.transport == BridgeClient.self)
        XCTAssertEqual(String(describing: BridgeSymbolVisibilityGuard.payloadBuilder), "BridgePayloadBuilder")
        XCTAssertEqual(BridgeSymbolVisibilityGuard.clientError, .bridgeUnavailable)
        XCTAssertEqual(BridgeSymbolVisibilityGuard.errorPayload.code, .invalidRequest)
        XCTAssertEqual(BridgeSymbolVisibilityGuard.errorPayload.message, "guard")
    }
}
