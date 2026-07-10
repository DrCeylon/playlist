import Foundation

/// Abstract navigation destinations mirrored from Python `AppRoute`.
public enum AppRoute: String, Codable, CaseIterable, Identifiable, Hashable, Sendable {
    case home = "home"
    case newPlaylist = "new_playlist"
    case preview = "preview"
    case `import` = "import"
    case history = "history"
    case historyDetail = "history_detail"
    case diagnostics = "diagnostics"
    case settings = "settings"
    case settingsTheme = "settings_theme"
    case settingsProvider = "settings_provider"
    case manualAcquisition = "manual_acquisition"
    case playlists = "playlists"
    case playlistDetail = "playlist_detail"
    case sync = "sync"
    case providers = "providers"

    public var id: String { rawValue }
}

/// Primary macOS sidebar destinations for the product shell.
public enum SidebarItem: String, CaseIterable, Identifiable, Hashable, Sendable {
    case home
    case newPlaylist
    case playlists
    case sync
    case providers
    case history
    case settings

    public var id: String { rawValue }

    public var title: String {
        switch self {
        case .home:
            return "Accueil"
        case .newPlaylist:
            return "Créer"
        case .playlists:
            return "Playlists"
        case .sync:
            return "Synchronisation"
        case .providers:
            return "Services musicaux"
        case .history:
            return "Historique"
        case .settings:
            return "Paramètres"
        }
    }

    public var systemImage: String {
        switch self {
        case .home:
            return "house"
        case .newPlaylist:
            return "plus.rectangle.on.rectangle"
        case .playlists:
            return "music.note.list"
        case .sync:
            return "arrow.triangle.2.circlepath"
        case .providers:
            return "music.note.house"
        case .history:
            return "clock"
        case .settings:
            return "gearshape"
        }
    }

    public var route: AppRoute {
        switch self {
        case .home:
            return .home
        case .newPlaylist:
            return .newPlaylist
        case .playlists:
            return .playlists
        case .sync:
            return .sync
        case .providers:
            return .providers
        case .history:
            return .history
        case .settings:
            return .settings
        }
    }
}
