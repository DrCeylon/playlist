import Combine
import Foundation

@MainActor
public final class ThemeManager: ObservableObject {
    public static let defaultThemeID = "apple_music_light"

    @Published public private(set) var active: Theme
    public let registry: ThemeRegistry

    private var subscribers: [ThemeObserver] = []

    public init(registry: ThemeRegistry, defaultThemeID: String = ThemeManager.defaultThemeID) throws {
        self.registry = registry
        self.active = try registry.get(defaultThemeID)
    }

    public convenience init() throws {
        try self.init(registry: ThemeRegistry.loadBundled())
    }

    public var themeOptions: [ThemeOption] {
        registry.list().map { $0.toOption() }
    }

    public func apply(themeID: String) throws {
        let theme = try registry.get(themeID)
        guard theme.id != active.id else { return }
        active = theme
        for observer in subscribers {
            observer.notify(theme: theme)
        }
    }

    public func subscribe(_ observer: ThemeObserver) {
        subscribers.append(observer)
    }

    public func unsubscribe(_ observer: ThemeObserver) {
        subscribers.removeAll { $0 === observer }
    }
}

/// Reference-type listener so unsubscribe can match by identity.
public final class ThemeObserver {
    private let handler: (Theme) -> Void

    public init(handler: @escaping (Theme) -> Void) {
        self.handler = handler
    }

    fileprivate func notify(theme: Theme) {
        handler(theme)
    }
}
