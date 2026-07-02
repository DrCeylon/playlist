import Foundation

public enum BridgeErrorCode: String, Codable, Sendable {
    case unknownCommand = "unknown_command"
    case invalidRequest = "invalid_request"
    case validationFailed = "validation_failed"
    case notConfigured = "not_configured"
    case engineError = "engine_error"
    case providerUnavailable = "provider_unavailable"
    case manualActionRequired = "manual_action_required"
}

public struct BridgeErrorPayload: Equatable, Sendable {
    public let code: BridgeErrorCode
    public let message: String

    public init(code: BridgeErrorCode, message: String) {
        self.code = code
        self.message = message
    }
}

public enum BridgeClientError: Error, Equatable {
    case processUnavailable
    case timeout
    case invalidResponse
    case bridgeUnavailable
    case bridge(BridgeErrorPayload)
}

public enum DiagnosticsServiceError: Error, Equatable {
    case bridgeUnavailable
    case timeout
    case invalidResponse
    case bridge(BridgeErrorPayload)
}

public enum SessionHistoryServiceError: Error, Equatable {
    case bridgeUnavailable
    case timeout
    case invalidResponse
    case bridge(BridgeErrorPayload)
}
