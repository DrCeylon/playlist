import Foundation

public enum ThemeValidation {
    static let requiredColorKeys: [String] = [
        "color.background.primary",
        "color.background.secondary",
        "color.background.elevated",
        "color.text.primary",
        "color.text.secondary",
        "color.text.tertiary",
        "color.accent.primary",
        "color.accent.secondary",
        "color.border.subtle",
        "color.status.success",
        "color.status.warning",
        "color.status.error",
        "color.status.info",
        "color.lab.accent",
    ]

    static let requiredTypographyKeys: [String] = [
        "font.largeTitle",
        "font.title",
        "font.headline",
        "font.body",
        "font.callout",
        "font.caption",
        "font.mono",
    ]

    static let requiredSpacingKeys: [String] = [
        "space.xs",
        "space.sm",
        "space.md",
        "space.lg",
        "space.xl",
        "space.xxl",
    ]

    static let requiredRadiusKeys: [String] = [
        "radius.sm",
        "radius.md",
        "radius.lg",
        "radius.xl",
    ]

    static let requiredShadowKeys: [String] = [
        "shadow.card",
        "shadow.elevated",
    ]

    public static func validate(theme: Theme) throws {
        if theme.id.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            throw ThemeError.validationFailed("L'identifiant du thème est requis.")
        }
        if theme.displayName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            throw ThemeError.validationFailed("Le nom affiché du thème est requis.")
        }
        if theme.version.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            throw ThemeError.validationFailed("La version du thème est requise.")
        }
        try validate(tokens: theme.tokens)
    }

    public static func validate(tokens: DesignTokens) throws {
        for key in requiredColorKeys where tokens.colors[key] == nil {
            throw ThemeError.validationFailed("Jeton de couleur requis manquant : \(key)")
        }
        for key in requiredTypographyKeys where tokens.typography[key] == nil {
            throw ThemeError.validationFailed("Jeton typographique requis manquant : \(key)")
        }
        for key in requiredSpacingKeys where tokens.spacing[key] == nil {
            throw ThemeError.validationFailed("Jeton d'espacement requis manquant : \(key)")
        }
        for key in requiredRadiusKeys where tokens.radius[key] == nil {
            throw ThemeError.validationFailed("Jeton de rayon requis manquant : \(key)")
        }
        for key in requiredShadowKeys where tokens.shadows[key] == nil {
            throw ThemeError.validationFailed("Jeton d'ombre requis manquant : \(key)")
        }

        for (key, value) in tokens.colors where !isValidColor(value) {
            throw ThemeError.validationFailed("Couleur invalide pour \(key) : \(value)")
        }
        for (key, value) in tokens.spacing where value < 0 {
            throw ThemeError.validationFailed("Espacement invalide pour \(key) : \(value)")
        }
        for (key, value) in tokens.radius where value < 0 {
            throw ThemeError.validationFailed("Rayon invalide pour \(key) : \(value)")
        }
    }

    public static func isValidColor(_ value: String) -> Bool {
        let pattern = #"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$"#
        return value.range(of: pattern, options: .regularExpression) != nil
    }
}
