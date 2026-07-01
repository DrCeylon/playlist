import Foundation

public enum BridgeCommand: String, Codable, Sendable {
    case listProviders = "list_providers"
    case validateGenerationRequest = "validate_generation_request"
    case generatePlaylist = "generate_playlist"
    case importPlaylist = "import_playlist"
    case diagnostics = "diagnostics"
    case continueManualAcquisition = "continue_manual_acquisition"
}

public enum BridgeEventType: String, Codable, Sendable {
    case started
    case progress
    case diagnostic
    case completed
    case error
    case manualAcquisitionRequired = "manual_acquisition_required"
}

public enum BridgeErrorCode: String, Codable, Sendable {
    case unknownCommand = "unknown_command"
    case invalidRequest = "invalid_request"
    case validationFailed = "validation_failed"
    case notConfigured = "not_configured"
    case engineError = "engine_error"
    case providerUnavailable = "provider_unavailable"
    case manualActionRequired = "manual_action_required"
}
