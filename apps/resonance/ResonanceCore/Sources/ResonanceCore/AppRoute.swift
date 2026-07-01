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

    public var id: String { rawValue }
}

/// Primary macOS sidebar destinations for the Phase 4.4 shell.
public enum SidebarItem: String, CaseIterable, Identifiable, Hashable, Sendable {
    case home
    case newPlaylist
    case history
    case laboratory
    case settings

    public var id: String { rawValue }

    public var title: String {
        switch self {
        case .home:
            return "Accueil"
        case .newPlaylist:
            return "Nouvelle Playlist"
        case .history:
            return "Historique"
        case .laboratory:
            return "Laboratoire"
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
        case .history:
            return "clock"
        case .laboratory:
            return "flask"
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
        case .history:
            return .history
        case .laboratory:
            return .diagnostics
        case .settings:
            return .settings
        }
    }
}
