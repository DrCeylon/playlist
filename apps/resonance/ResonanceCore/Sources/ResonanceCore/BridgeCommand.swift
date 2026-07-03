import Foundation

public enum BridgeCommand: String, Codable, Sendable {
    case listProviders = "list_providers"
    case validateGenerationRequest = "validate_generation_request"
    case generatePlaylist = "generate_playlist"
    case importPlaylist = "import_playlist"
    case diagnostics = "diagnostics"
    case continueManualAcquisition = "continue_manual_acquisition"
    case listHistory = "list_history"
    case getHistorySession = "get_history_session"
    case deleteHistorySession = "delete_history_session"
    case clearHistory = "clear_history"
    case replayGeneration = "replay_generation"
    case exportHistorySession = "export_history_session"
    case autocompleteSearch = "autocomplete_search"
}

public enum BridgeEventType: String, Codable, Sendable {
    case started
    case progress
    case diagnostic
    case completed
    case error
    case manualAcquisitionRequired = "manual_acquisition_required"
}
