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
    case probeManualAcquisition = "probe_manual_acquisition"
    case retryImportTracks = "retry_import_tracks"
    case listManagedPlaylists = "list_managed_playlists"
    case getManagedPlaylist = "get_managed_playlist"
    case syncManagedPlaylist = "sync_managed_playlist"
    case planSync = "plan_sync"
    case listRemotePlaylists = "list_remote_playlists"
    case getRemotePlaylist = "get_remote_playlist"
    case importRemotePlaylist = "import_remote_playlist"
    case applySync = "apply_sync"
    case providerAuthStatus = "provider_auth_status"
    case providerConnect = "provider_connect"
    case providerDisconnect = "provider_disconnect"
    case loadRemotePlaylistFromFile = "load_remote_playlist_from_file"
}

public enum BridgeEventType: String, Codable, Sendable {
    case started
    case progress
    case diagnostic
    case completed
    case error
    case manualAcquisitionRequired = "manual_acquisition_required"
    case trackProgress = "track_progress"
}
