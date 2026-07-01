import Foundation

public final class ThemeRegistry: @unchecked Sendable {
    private var themes: [String: Theme]

    public init(themes: [Theme] = []) {
        self.themes = Dictionary(uniqueKeysWithValues: themes.map { ($0.id, $0) })
    }

    public static func loadBundled() throws -> ThemeRegistry {
        try loadBundled(bundle: .module)
    }

    public static func loadBundled(bundle: Bundle) throws -> ThemeRegistry {
        let definitions = try ThemeLoader.loadBundledDefinitions(bundle: bundle)
        let resolved = try ThemeLoader.resolve(definitions)
        let registry = ThemeRegistry()
        for theme in resolved {
            try registry.register(theme)
        }
        return registry
    }

    public func register(_ theme: Theme) throws {
        try ThemeValidation.validate(theme: theme)
        themes[theme.id] = theme
    }

    public func get(_ themeID: String) throws -> Theme {
        guard let theme = themes[themeID] else {
            throw ThemeError.notFound(themeID)
        }
        return theme
    }

    public func list() -> [Theme] {
        themes.keys.sorted().compactMap { themes[$0] }
    }
}
