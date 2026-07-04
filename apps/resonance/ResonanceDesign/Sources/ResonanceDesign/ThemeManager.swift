import Combine
import Foundation
import ResonanceCore
import SwiftUI

@MainActor
public final class ThemeManager: ObservableObject {
    public nonisolated static let systemThemeID = "system"
    public nonisolated static let defaultThemeID = systemThemeID

    private nonisolated static let preferencesKey = "resonance.selectedThemeID"
    private nonisolated static let lightThemeID = "apple_music_light"
    private nonisolated static let darkThemeID = "apple_music_dark"

    private static let pickerOrder = [
        systemThemeID,
        lightThemeID,
        darkThemeID,
        "classic_winamp_inspired",
    ]

    @Published public private(set) var active: Theme
    @Published public private(set) var selectedThemeID: String
    public let registry: ThemeRegistry

    private var subscribers: [ThemeObserver] = []
    private var resolvedColorScheme: ColorScheme = .light

    public init(registry: ThemeRegistry, defaultThemeID: String = ThemeManager.defaultThemeID) throws {
        self.registry = registry
        let stored = UserDefaults.standard.string(forKey: Self.preferencesKey)
        let initialSelection = stored ?? defaultThemeID
        selectedThemeID = initialSelection
        let resolvedThemeID = Self.resolveThemeID(
            selectedThemeID: initialSelection,
            colorScheme: .light
        )
        active = try registry.get(resolvedThemeID)
    }

    public convenience init() throws {
        try self.init(registry: ThemeRegistry.loadBundled())
    }

    public var themeOptions: [ThemeOption] {
        let bundled = Dictionary(uniqueKeysWithValues: registry.list().map { ($0.id, $0) })
        return Self.pickerOrder.compactMap { themeID in
            if themeID == Self.systemThemeID {
                return Self.systemThemeOption(registry: registry)
            }
            return bundled[themeID]?.toOption()
        }
    }

    public var activeDisplayName: String {
        if selectedThemeID == Self.systemThemeID {
            return "Système (\(active.displayName))"
        }
        return active.displayName
    }

    public func apply(themeID: String) throws {
        selectedThemeID = themeID
        UserDefaults.standard.set(themeID, forKey: Self.preferencesKey)
        try refreshActiveTheme()
    }

    public func updateColorScheme(_ colorScheme: ColorScheme) {
        let changed = colorScheme != resolvedColorScheme
        resolvedColorScheme = colorScheme
        guard selectedThemeID == Self.systemThemeID, changed else { return }
        try? refreshActiveTheme()
    }

    public func subscribe(_ observer: ThemeObserver) {
        subscribers.append(observer)
    }

    public func unsubscribe(_ observer: ThemeObserver) {
        subscribers.removeAll { $0 === observer }
    }

    nonisolated private static func resolveThemeID(selectedThemeID: String, colorScheme: ColorScheme) -> String {
        if selectedThemeID == systemThemeID {
            return colorScheme == .dark ? darkThemeID : lightThemeID
        }
        return selectedThemeID
    }

    private func refreshActiveTheme() throws {
        let resolvedID = Self.resolveThemeID(
            selectedThemeID: selectedThemeID,
            colorScheme: resolvedColorScheme
        )
        let theme = try registry.get(resolvedID)
        guard theme.id != active.id else { return }
        active = theme
        for observer in subscribers {
            observer.notify(theme: theme)
        }
    }

    private static func systemThemeOption(registry: ThemeRegistry) -> ThemeOption {
        let light = try? registry.get(lightThemeID)
        let dark = try? registry.get(darkThemeID)
        return ThemeOption(
            themeID: systemThemeID,
            displayName: "Système",
            previewBackground: light?.tokens.colors["color.background.primary", default: ""] ?? "",
            previewAccent: dark?.tokens.colors["color.background.primary", default: ""] ?? ""
        )
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
