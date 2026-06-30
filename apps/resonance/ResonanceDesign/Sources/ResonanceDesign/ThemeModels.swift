import Foundation

public struct DesignTokens: Hashable, Sendable {
    public let colors: [String: String]
    public let typography: [String: String]
    public let spacing: [String: Int]
    public let radius: [String: Int]
    public let shadows: [String: String]

    public init(
        colors: [String: String] = [:],
        typography: [String: String] = [:],
        spacing: [String: Int] = [:],
        radius: [String: Int] = [:],
        shadows: [String: String] = [:]
    ) {
        self.colors = colors
        self.typography = typography
        self.spacing = spacing
        self.radius = radius
        self.shadows = shadows
    }

    public func merged(with override: DesignTokens) -> DesignTokens {
        DesignTokens(
            colors: colors.merging(override.colors) { _, new in new },
            typography: typography.merging(override.typography) { _, new in new },
            spacing: spacing.merging(override.spacing) { _, new in new },
            radius: radius.merging(override.radius) { _, new in new },
            shadows: shadows.merging(override.shadows) { _, new in new }
        )
    }

    public static let empty = DesignTokens()
}

public struct Theme: Identifiable, Hashable, Sendable {
    public let id: String
    public let displayName: String
    public let version: String
    public let tokens: DesignTokens
    public let metadata: [String: String]
    public let extends: String?

    public init(
        id: String,
        displayName: String,
        version: String,
        tokens: DesignTokens,
        metadata: [String: String] = [:],
        extends: String? = nil
    ) {
        self.id = id
        self.displayName = displayName
        self.version = version
        self.tokens = tokens
        self.metadata = metadata
        self.extends = extends
    }
}

public struct ThemeDefinition: Hashable, Sendable {
    public let id: String
    public let displayName: String
    public let version: String
    public let tokens: DesignTokens
    public let metadata: [String: String]
    public let extends: String?

    public init(
        id: String,
        displayName: String,
        version: String,
        tokens: DesignTokens,
        metadata: [String: String] = [:],
        extends: String? = nil
    ) {
        self.id = id
        self.displayName = displayName
        self.version = version
        self.tokens = tokens
        self.metadata = metadata
        self.extends = extends
    }
}

public enum ThemeError: Error, Equatable, Sendable {
    case notFound(String)
    case loadFailed(String)
    case validationFailed(String)
    case circularInheritance(String)
}

extension Theme {
    public func toOption() -> ThemeOption {
        ThemeOption(
            themeID: id,
            displayName: displayName,
            previewBackground: tokens.colors["color.background.primary", default: ""],
            previewAccent: tokens.colors["color.accent.primary", default: ""]
        )
    }
}
