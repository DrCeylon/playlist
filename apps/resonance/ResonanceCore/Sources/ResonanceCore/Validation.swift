import Foundation

public struct ValidationError: Hashable, Codable, Sendable {
    public let field: String
    public let message: String

    public init(field: String, message: String) {
        self.field = field
        self.message = message
    }
}

public struct ValidationResult: Sendable {
    public let errors: [ValidationError]

    public init(errors: [ValidationError] = []) {
        self.errors = errors
    }

    public var isValid: Bool {
        errors.isEmpty
    }

    public func merged(with other: ValidationResult) -> ValidationResult {
        ValidationResult(errors: errors + other.errors)
    }

    public static func merge(_ results: ValidationResult...) -> ValidationResult {
        results.reduce(ValidationResult()) { $0.merged(with: $1) }
    }
}

public enum PlaylistGenerationValidator {
    public static func validateName(_ name: String) -> ValidationResult {
        let trimmed = name.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty {
            return ValidationResult(errors: [
                ValidationError(field: "name", message: "Le nom de la playlist est obligatoire."),
            ])
        }
        if trimmed.count > 120 {
            return ValidationResult(errors: [
                ValidationError(field: "name", message: "Le nom ne doit pas dépasser 120 caractères."),
            ])
        }
        return ValidationResult()
    }

    public static func validateProviderID(_ providerID: ProviderID) -> ValidationResult {
        ValidationResult()
    }

    public static func validateSeedsOrKeywords(
        seeds: [SeedReference],
        keywords: [String]
    ) -> ValidationResult {
        let hasSeed = seeds.contains {
            !$0.artist.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                || !$0.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        }
        let hasKeywords = keywords.contains { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        if hasSeed || hasKeywords {
            return ValidationResult()
        }
        return ValidationResult(errors: [
            ValidationError(
                field: "seeds",
                message: "Au moins une graine (artiste/morceau) ou un mot-clé est requis."
            ),
        ])
    }

    public static func validateTargetSize(
        targetTrackCount: Int?,
        targetDurationMinutes: Int?
    ) -> ValidationResult {
        if targetTrackCount == nil && targetDurationMinutes == nil {
            return ValidationResult(errors: [
                ValidationError(
                    field: "target_track_count",
                    message: "Le nombre de morceaux ou la durée cible est requis."
                ),
            ])
        }
        var errors: [ValidationError] = []
        if let targetTrackCount, targetTrackCount <= 0 {
            errors.append(
                ValidationError(
                    field: "target_track_count",
                    message: "Le nombre de morceaux doit être positif."
                )
            )
        }
        if let targetDurationMinutes, targetDurationMinutes <= 0 {
            errors.append(
                ValidationError(
                    field: "target_duration_minutes",
                    message: "La durée cible doit être positive."
                )
            )
        }
        return ValidationResult(errors: errors)
    }

    public static func validateExclusionRule(_ rule: ExclusionRule) -> ValidationResult {
        if rule.value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return ValidationResult(errors: [
                ValidationError(
                    field: "exclusions.value",
                    message: "La valeur d'exclusion ne peut pas être vide."
                ),
            ])
        }
        return ValidationResult()
    }

    public static func validateEnergyCurve(_ curve: EnergyCurveOption) -> ValidationResult {
        if EnergyCurveProfile.allCases.contains(curve.profile) {
            return ValidationResult()
        }
        return ValidationResult(errors: [
            ValidationError(
                field: "energy_curve.profile",
                message: "Profil d'énergie invalide : \(curve.profile.rawValue)."
            ),
        ])
    }

    public static func validate(_ request: PlaylistGenerationRequest) -> ValidationResult {
        var results = [
            validateName(request.name),
            validateProviderID(request.providerID),
            validateSeedsOrKeywords(seeds: request.seeds, keywords: request.keywords),
            validateTargetSize(
                targetTrackCount: request.targetTrackCount,
                targetDurationMinutes: request.targetDurationMinutes
            ),
            validateEnergyCurve(request.energyCurve),
        ]
        for rule in request.exclusions {
            results.append(validateExclusionRule(rule))
        }
        return ValidationResult.merge(results)
    }
}
