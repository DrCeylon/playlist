import Foundation

public enum ThemeLoader {
    private static let maxThemeFileBytes = 256 * 1024

    public static func loadBundledDefinitions(bundle: Bundle = .module) throws -> [ThemeDefinition] {
        guard let themesURL = bundle.resourceURL?.appendingPathComponent("themes", isDirectory: true) else {
            throw ThemeError.loadFailed("Dossier de thèmes embarqués introuvable.")
        }
        let urls = try FileManager.default.contentsOfDirectory(
            at: themesURL,
            includingPropertiesForKeys: nil
        ).filter { $0.pathExtension == "json" && $0.lastPathComponent.hasSuffix(".theme.json") }
        if urls.isEmpty {
            throw ThemeError.loadFailed("Aucun thème embarqué trouvé.")
        }
        return try urls.sorted { $0.lastPathComponent < $1.lastPathComponent }.map { url in
            try loadThemeFile(at: url)
        }
    }

    public static func loadThemeFile(at url: URL) throws -> ThemeDefinition {
        let data = try Data(contentsOf: url)
        if data.count > maxThemeFileBytes {
            throw ThemeError.loadFailed("Fichier de thème trop volumineux : \(url.lastPathComponent)")
        }
        let payload = try JSONDecoder().decode(ThemeFilePayload.self, from: data)
        return try payload.toDefinition(source: url.lastPathComponent)
    }

    public static func resolve(_ definitions: [ThemeDefinition]) throws -> [Theme] {
        let byID = Dictionary(uniqueKeysWithValues: definitions.map { ($0.id, $0) })
        if byID.count != definitions.count {
            throw ThemeError.loadFailed("Des identifiants de thème en double ont été détectés.")
        }

        var resolved: [String: Theme] = [:]
        var resolving: Set<String> = []

        func resolveOne(_ themeID: String) throws -> Theme {
            if let theme = resolved[themeID] {
                return theme
            }
            guard let definition = byID[themeID] else {
                throw ThemeError.loadFailed("Thème parent introuvable : \(themeID)")
            }
            if resolving.contains(themeID) {
                throw ThemeError.circularInheritance(themeID)
            }
            resolving.insert(themeID)

            var tokens = definition.tokens
            if let parentID = definition.extends {
                let parent = try resolveOne(parentID)
                tokens = parent.tokens.merged(with: definition.tokens)
            }

            let theme = Theme(
                id: definition.id,
                displayName: definition.displayName,
                version: definition.version,
                tokens: tokens,
                metadata: definition.metadata,
                extends: definition.extends
            )
            resolving.remove(themeID)
            resolved[themeID] = theme
            return theme
        }

        return try definitions.map { try resolveOne($0.id) }
    }
}

private struct ThemeFilePayload: Decodable {
    let id: String
    let displayName: String
    let version: String
    let extends: String?
    let tokens: ThemeTokensPayload?
    let metadata: [String: String]?

    func toDefinition(source: String) throws -> ThemeDefinition {
        let trimmedID = id.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedName = displayName.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedVersion = version.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmedID.isEmpty || trimmedName.isEmpty || trimmedVersion.isEmpty {
            throw ThemeError.loadFailed("Champs requis manquants dans \(source)")
        }
        return ThemeDefinition(
            id: trimmedID,
            displayName: trimmedName,
            version: trimmedVersion,
            tokens: tokens?.toDesignTokens() ?? .empty,
            metadata: metadata ?? [:],
            extends: extends?.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty
        )
    }
}

private struct ThemeTokensPayload: Decodable {
    let colors: [String: String]?
    let typography: [String: String]?
    let spacing: [String: Int]?
    let radius: [String: Int]?
    let shadows: [String: String]?

    func toDesignTokens() -> DesignTokens {
        DesignTokens(
            colors: colors ?? [:],
            typography: typography ?? [:],
            spacing: spacing ?? [:],
            radius: radius ?? [:],
            shadows: shadows ?? [:]
        )
    }
}

private extension String {
    var nilIfEmpty: String? {
        isEmpty ? nil : self
    }
}
